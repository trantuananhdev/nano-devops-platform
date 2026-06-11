# verify-t56.ps1 - Static checks for Ansible Dual-User configuration (T-56)
$ErrorActionPreference = "Stop"

Write-Host "================================================================"
Write-Host "[T-56] Running static checks for Ansible Dual-User configuration..."
Write-Host "================================================================"

$allPassed = $true

# 1. Check .env
$envPath = ".env"
$envPattern = "tutinhhao@ACER_HOST"
if (Test-Path $envPath) {
    $match = Select-String -Path $envPath -Pattern $envPattern -SimpleMatch
    if ($match) {
        Write-Host "[OK] Check SSH comments in .env"
    } else {
        Write-Host "[FAIL] Check SSH comments in .env : Pattern '$envPattern' not found"
        $allPassed = $false
    }
} else {
    Write-Host "[FAIL] Check SSH comments in .env : File .env not found"
    $allPassed = $false
}

# 2. Check Vagrantfile
$vgPath = "Vagrantfile"
$vgPattern = "ansible-test-users"
if (Test-Path $vgPath) {
    $match = Select-String -Path $vgPath -Pattern $vgPattern -SimpleMatch
    if ($match) {
        Write-Host "[OK] Check test-users command in Vagrantfile"
    } else {
        Write-Host "[FAIL] Check test-users command in Vagrantfile : Pattern '$vgPattern' not found"
        $allPassed = $false
    }
} else {
    Write-Host "[FAIL] Check test-users command in Vagrantfile : File Vagrantfile not found"
    $allPassed = $false
}

# 3. Check deploy.sh
$depPath = "project_devops/apps/ansible-ubuntu/deploy.sh"
$depPattern = 'ACER_USER="tutinhhao"'
if (Test-Path $depPath) {
    $match = Select-String -Path $depPath -Pattern $depPattern -SimpleMatch
    if ($match) {
        Write-Host "[OK] Check ACER_USER=tutinhhao in deploy.sh"
    } else {
        Write-Host "[FAIL] Check ACER_USER=tutinhhao in deploy.sh : Pattern '$depPattern' not found"
        $allPassed = $false
    }
} else {
    Write-Host "[FAIL] Check ACER_USER=tutinhhao in deploy.sh : File deploy.sh not found"
    $allPassed = $false
}

# 4. Check teardown.yml
$tdPath = "project_devops/apps/ansible-ubuntu/teardown.yml"
$tdPattern = "become: true"
if (Test-Path $tdPath) {
    $match = Select-String -Path $tdPath -Pattern $tdPattern -SimpleMatch
    if ($match) {
        Write-Host "[OK] Check become: true in teardown.yml"
    } else {
        Write-Host "[FAIL] Check become: true in teardown.yml : Pattern '$tdPattern' not found"
        $allPassed = $false
    }
} else {
    Write-Host "[FAIL] Check become: true in teardown.yml : File teardown.yml not found"
    $allPassed = $false
}

Write-Host "================================================================"
if ($allPassed) {
    Write-Host "SUCCESS: ALL STATIC CHECKS PASSED! Ready for dual-user model."
    $exitCode = 0
} else {
    Write-Host "ERROR: SOME CHECKS FAILED! Please review the logs above."
    $exitCode = 1
}

Exit $exitCode
