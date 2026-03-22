package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"runtime"
	"strings"
	"syscall"
	"time"
)

// ─────────────────────────────────────────────
// Docker Unix Socket Client (no SDK, zero deps)
// ─────────────────────────────────────────────

func dockerClient() *http.Client {
	return &http.Client{
		Transport: &http.Transport{
			DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
				return (&net.Dialer{}).DialContext(ctx, "unix", "/var/run/docker.sock")
			},
		},
		Timeout: 10 * time.Second,
	}
}

func dockerGet(ctx context.Context, path string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, "http://docker"+path, nil)
	if err != nil {
		return nil, err
	}
	return dockerClient().Do(req)
}

func dockerPost(ctx context.Context, path string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, "http://docker"+path, nil)
	if err != nil {
		return nil, err
	}
	return dockerClient().Do(req)
}

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

type AgentConfig struct {
	BrainURL        string
	NodeName        string
	Environment     string
	Version         string
	CommandPort     string
	MonitorInterval time.Duration
	LogTailLines    string
	CPUAlertPct     float64
	RAMAlertPct     float64
}

type DockerEvent struct {
	Type   string `json:"Type"`
	Action string `json:"Action"`
	Actor  struct {
		ID         string            `json:"ID"`
		Attributes map[string]string `json:"Attributes"`
	} `json:"Actor"`
	Time int64 `json:"time"`
}

type DockerContainer struct {
	ID    string   `json:"Id"`
	Names []string `json:"Names"`
	Image string   `json:"Image"`
}

type DockerStats struct {
	CPUStats struct {
		CPUUsage struct {
			TotalUsage    uint64   `json:"total_usage"`
			PercpuUsage   []uint64 `json:"percpu_usage"`
		} `json:"cpu_usage"`
		SystemUsage uint64 `json:"system_cpu_usage"`
		OnlineCPUs  int    `json:"online_cpus"`
	} `json:"cpu_stats"`
	PreCPUStats struct {
		CPUUsage struct {
			TotalUsage uint64 `json:"total_usage"`
		} `json:"cpu_usage"`
		SystemUsage uint64 `json:"system_cpu_usage"`
	} `json:"precpu_stats"`
	MemoryStats struct {
		Usage uint64 `json:"usage"`
		Limit uint64 `json:"limit"`
	} `json:"memory_stats"`
}

type IncidentPayload struct {
	Type          string            `json:"type"`
	NodeName      string            `json:"nodeName"`
	ContainerID   string            `json:"containerId"`
	ContainerName string            `json:"containerName"`
	Image         string            `json:"image"`
	Action        string            `json:"action"`
	ExitCode      string            `json:"exitCode"`
	Logs          string            `json:"logs"`
	Timestamp     string            `json:"timestamp"`
	SensorVersion string            `json:"sensorVersion"`
}

type MetricPayload struct {
	Type          string             `json:"type"`
	NodeName      string             `json:"nodeName"`
	Timestamp     string             `json:"timestamp"`
	SensorVersion string             `json:"sensorVersion"`
	Containers    []ContainerMetrics `json:"containers"`
}

type ContainerMetrics struct {
	ContainerID   string  `json:"containerId"`
	ContainerName string  `json:"containerName"`
	Image         string  `json:"image"`
	CPUPercent    float64 `json:"cpuPercent"`
	RAMPercent    float64 `json:"ramPercent"`
	RAMUsageMB    float64 `json:"ramUsageMB"`
	RAMLimitMB    float64 `json:"ramLimitMB"`
	AlertCPU      bool    `json:"alertCpu"`
	AlertRAM      bool    `json:"alertRam"`
}

type CommandRequest struct {
	Action      string `json:"action"`
	ContainerID string `json:"containerId"`
}

type CommandResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

// ─────────────────────────────────────────────
// Config
// ─────────────────────────────────────────────

func loadConfig() AgentConfig {
	interval, _ := time.ParseDuration(getEnv("MONITOR_INTERVAL", "30s"))
	return AgentConfig{
		BrainURL:        getEnv("BRAIN_URL", "http://platform-agentic-ai:3000/v1/incidents/report"),
		NodeName:        getEnv("NODE_NAME", "nano-devops-node"),
		Environment:     getEnv("ENV", "production"),
		Version:         "0.3.0",
		CommandPort:     getEnv("COMMAND_PORT", "8080"),
		MonitorInterval: interval,
		LogTailLines:    getEnv("LOG_TAIL_LINES", "100"),
		CPUAlertPct:     80.0,
		RAMAlertPct:     85.0,
	}
}

// ─────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────

func main() {
	cfg := loadConfig()

	fmt.Printf("👻 Ghost Engineer Sensor v%s\n", cfg.Version)
	fmt.Printf("🚀 Node: %s | Env: %s\n", cfg.NodeName, cfg.Environment)
	fmt.Printf("🧠 Brain: %s\n", cfg.BrainURL)
	fmt.Printf("🖥️  Go: %s | %s/%s\n", runtime.Version(), runtime.GOOS, runtime.GOARCH)
	fmt.Println("📡 Using Docker Unix Socket (no SDK)")

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-stop
		fmt.Println("\n🛑 Shutting down...")
		cancel()
	}()

	go runEventLoop(ctx, cfg)
	go runMetricLoop(ctx, cfg)
	go runCommandServer(ctx, cfg)
	go runHealthServer(cfg)

	<-ctx.Done()
	fmt.Println("✅ Ghost Sensor stopped.")
}

// ─────────────────────────────────────────────
// A. Event Loop — stream docker events
// ─────────────────────────────────────────────

func runEventLoop(ctx context.Context, cfg AgentConfig) {
	for {
		select {
		case <-ctx.Done():
			return
		default:
			if err := streamEvents(ctx, cfg); err != nil {
				log.Printf("⚠️  Event stream error: %v. Retrying in 5s...", err)
				select {
				case <-ctx.Done():
					return
				case <-time.After(5 * time.Second):
				}
			}
		}
	}
}

func streamEvents(ctx context.Context, cfg AgentConfig) error {
	client := &http.Client{
		Transport: &http.Transport{
			DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
				return (&net.Dialer{}).DialContext(ctx, "unix", "/var/run/docker.sock")
			},
		},
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet,
		"http://docker/events?filters=%7B%22type%22%3A%7B%22container%22%3Atrue%7D%2C%22event%22%3A%7B%22die%22%3Atrue%2C%22oom%22%3Atrue%7D%7D",
		nil)
	if err != nil {
		return err
	}

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	fmt.Println("🕵️  Listening for container die/oom events...")

	scanner := bufio.NewScanner(resp.Body)
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}
		var event DockerEvent
		if err := json.Unmarshal([]byte(line), &event); err != nil {
			continue
		}
		if event.Type == "container" && (event.Action == "die" || event.Action == "oom") {
			go handleCrashEvent(ctx, event, cfg)
		}
	}
	return scanner.Err()
}

func handleCrashEvent(ctx context.Context, event DockerEvent, cfg AgentConfig) {
	containerID := event.Actor.ID
	containerName := event.Actor.Attributes["name"]
	image := event.Actor.Attributes["image"]
	exitCode := event.Actor.Attributes["exitCode"]

	fmt.Printf("\n🔥 [INCIDENT] action=%s container=%s exitCode=%s\n",
		event.Action, containerName, exitCode)

	logs := fetchLogs(ctx, containerID, cfg.LogTailLines)

	reportToBrain(cfg, IncidentPayload{
		Type:          "crash",
		NodeName:      cfg.NodeName,
		ContainerID:   containerID,
		ContainerName: containerName,
		Image:         image,
		Action:        event.Action,
		ExitCode:      exitCode,
		Logs:          logs,
		Timestamp:     time.Now().Format(time.RFC3339),
		SensorVersion: cfg.Version,
	})
}

func fetchLogs(ctx context.Context, containerID, tail string) string {
	resp, err := dockerGet(ctx, fmt.Sprintf(
		"/containers/%s/logs?stdout=1&stderr=1&tail=%s&timestamps=1",
		containerID, tail,
	))
	if err != nil {
		return ""
	}
	defer resp.Body.Close()
	buf := new(bytes.Buffer)
	_, _ = io.Copy(buf, resp.Body)
	return buf.String()
}

// ─────────────────────────────────────────────
// B. Metric Loop
// ─────────────────────────────────────────────

func runMetricLoop(ctx context.Context, cfg AgentConfig) {
	ticker := time.NewTicker(cfg.MonitorInterval)
	defer ticker.Stop()
	fmt.Printf("📊 Metric loop every %s (CPU>%.0f%% RAM>%.0f%%)\n",
		cfg.MonitorInterval, cfg.CPUAlertPct, cfg.RAMAlertPct)

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			collectAndReport(ctx, cfg)
		}
	}
}

func collectAndReport(ctx context.Context, cfg AgentConfig) {
	resp, err := dockerGet(ctx, "/containers/json")
	if err != nil {
		log.Printf("⚠️  List containers error: %v", err)
		return
	}
	defer resp.Body.Close()

	var containers []DockerContainer
	if err := json.NewDecoder(resp.Body).Decode(&containers); err != nil {
		return
	}

	var metrics []ContainerMetrics
	hasAlert := false

	for _, c := range containers {
		m, err := getContainerMetrics(ctx, c, cfg)
		if err != nil {
			continue
		}
		metrics = append(metrics, m)
		if m.AlertCPU || m.AlertRAM {
			hasAlert = true
			fmt.Printf("🚨 [ALERT] %s CPU=%.1f%% RAM=%.1f%%\n",
				m.ContainerName, m.CPUPercent, m.RAMPercent)
		}
	}

	if !hasAlert {
		return
	}

	reportToBrain(cfg, MetricPayload{
		Type:          "metrics",
		NodeName:      cfg.NodeName,
		Timestamp:     time.Now().Format(time.RFC3339),
		SensorVersion: cfg.Version,
		Containers:    metrics,
	})
}

func getContainerMetrics(ctx context.Context, c DockerContainer, cfg AgentConfig) (ContainerMetrics, error) {
	name := c.ID[:12]
	if len(c.Names) > 0 {
		name = strings.TrimPrefix(c.Names[0], "/")
	}

	resp, err := dockerGet(ctx, fmt.Sprintf("/containers/%s/stats?stream=false", c.ID))
	if err != nil {
		return ContainerMetrics{}, err
	}
	defer resp.Body.Close()

	var stats DockerStats
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return ContainerMetrics{}, err
	}

	cpuDelta := float64(stats.CPUStats.CPUUsage.TotalUsage - stats.PreCPUStats.CPUUsage.TotalUsage)
	sysDelta := float64(stats.CPUStats.SystemUsage - stats.PreCPUStats.SystemUsage)
	numCPU := float64(stats.CPUStats.OnlineCPUs)
	if numCPU == 0 {
		numCPU = float64(len(stats.CPUStats.CPUUsage.PercpuUsage))
	}
	cpuPct := 0.0
	if sysDelta > 0 {
		cpuPct = (cpuDelta / sysDelta) * numCPU * 100.0
	}

	ramUsage := float64(stats.MemoryStats.Usage) / 1024 / 1024
	ramLimit := float64(stats.MemoryStats.Limit) / 1024 / 1024
	ramPct := 0.0
	if ramLimit > 0 {
		ramPct = (ramUsage / ramLimit) * 100
	}

	return ContainerMetrics{
		ContainerID:   c.ID,
		ContainerName: name,
		Image:         c.Image,
		CPUPercent:    cpuPct,
		RAMPercent:    ramPct,
		RAMUsageMB:    ramUsage,
		RAMLimitMB:    ramLimit,
		AlertCPU:      cpuPct >= cfg.CPUAlertPct,
		AlertRAM:      ramPct >= cfg.RAMAlertPct,
	}, nil
}

// ─────────────────────────────────────────────
// C. Command Server
// ─────────────────────────────────────────────

func runCommandServer(ctx context.Context, cfg AgentConfig) {
	mux := http.NewServeMux()

	mux.HandleFunc("/command", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var cmd CommandRequest
		if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
			respondJSON(w, http.StatusBadRequest, CommandResponse{false, "invalid JSON"})
			return
		}

		fmt.Printf("📨 [COMMAND] action=%s container=%s\n", cmd.Action, cmd.ContainerID)

		validActions := map[string]bool{"restart": true, "stop": true, "start": true, "kill": true}
		if !validActions[cmd.Action] {
			respondJSON(w, http.StatusBadRequest, CommandResponse{false, "unknown action: " + cmd.Action})
			return
		}

		resp, err := dockerPost(ctx, fmt.Sprintf("/containers/%s/%s", cmd.ContainerID, cmd.Action))
		if err != nil || (resp.StatusCode >= 400) {
			msg := "command failed"
			if err != nil {
				msg = err.Error()
			}
			respondJSON(w, http.StatusInternalServerError, CommandResponse{false, msg})
			return
		}
		defer resp.Body.Close()

		fmt.Printf("✅ [COMMAND] %s done\n", cmd.Action)
		respondJSON(w, http.StatusOK, CommandResponse{true, cmd.Action + " succeeded"})
	})

	addr := ":" + cfg.CommandPort
	fmt.Printf("🎮 Command server on %s\n", addr)
	srv := &http.Server{Addr: addr, Handler: mux}
	go func() {
		<-ctx.Done()
		_ = srv.Shutdown(context.Background())
	}()
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Printf("⚠️  Command server: %v", err)
	}
}

// ─────────────────────────────────────────────
// D. Health Server
// ─────────────────────────────────────────────

func runHealthServer(cfg AgentConfig) {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"status":"ok","node":"%s","version":"%s"}`,
			cfg.NodeName, cfg.Version)
	})
	fmt.Println("❤️  Health probe on :8081/health")
	if err := http.ListenAndServe(":8081", mux); err != nil {
		log.Printf("⚠️  Health server: %v", err)
	}
}

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

var (
	lastReportFailure time.Time
	failureCount       int
)

func reportToBrain(cfg AgentConfig, payload any) {
	// Circuit breaker: if Brain is down, don't spam and cause DNS lookup failures
	if failureCount >= 3 && time.Since(lastReportFailure) < 1*time.Minute {
		return
	}

	data, err := json.Marshal(payload)
	if err != nil {
		return
	}
	req, err := http.NewRequest(http.MethodPost, cfg.BrainURL, bytes.NewBuffer(data))
	if err != nil {
		return
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "Ghost-Sensor/"+cfg.Version)
	req.Header.Set("X-Node-Name", cfg.NodeName)

	// Shorter timeout for reporting to prevent blocking
	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("❌ Brain report failed: %v", err)
		lastReportFailure = time.Now()
		failureCount++
		return
	}
	defer resp.Body.Close()

	failureCount = 0 // Reset on success
	fmt.Printf("🧠 Brain acknowledged HTTP %d\n", resp.StatusCode)
}

func respondJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func getEnv(key, fallback string) string {
	if v, ok := os.LookupEnv(key); ok {
		return v
	}
	return fallback
}