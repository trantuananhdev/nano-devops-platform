#!/bin/bash

# --- Xử lý cho folder docs-ai-context ---
echo "Đang gom dữ liệu vào docs-ai-context/final_ai_context.md..."
TARGET_DIR_1="./docs-ai-context"
OUTPUT_FILE_1="get_final_ai_context.md"

find "$TARGET_DIR_1" -maxdepth 4 -not -path "*/.*" -not -path "./node_modules/*" -not -name "$OUTPUT_FILE_1" -type f -exec sh -c '
    echo "=================================================="
    echo "SOURCE_PATH: {}"
    echo "=================================================="
    cat "{}"
    echo -e "\n\n"
' \; > "$TARGET_DIR_1/$OUTPUT_FILE_1"

# --- Xử lý cho folder docs-devops ---
echo "Đang gom dữ liệu vào docs-devops/final_devops_context.md..."
TARGET_DIR_2="./docs-devops"
OUTPUT_FILE_2="get_final_devops_context.md"

find "$TARGET_DIR_2" -maxdepth 4 -not -path "*/.*" -not -path "./node_modules/*" -not -name "$OUTPUT_FILE_2" -type f -exec sh -c '
    echo "=================================================="
    echo "SOURCE_PATH: {}"
    echo "=================================================="
    cat "{}"
    echo -e "\n\n"
' \; > "$TARGET_DIR_2/$OUTPUT_FILE_2"

TARGET_DIR_3="./ai-system"
OUTPUT_FILE_3="get_final_aisystem_context.md"

find "$TARGET_DIR_3" -maxdepth 4 -not -path "*/.*" -not -path "./node_modules/*" -not -name "$OUTPUT_FILE_3" -type f -exec sh -c '
    echo "=================================================="
    echo "SOURCE_PATH: {}"
    echo "=================================================="
    cat "{}"
    echo -e "\n\n"
' \; > "$TARGET_DIR_3/$OUTPUT_FILE_3"

echo "Xong! Check trong 2 folder nhé bạn."