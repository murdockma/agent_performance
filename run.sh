validate_date() {
  local input_date="$1"
  if [ -n "$input_date" ] && date -d "$input_date" >/dev/null 2>&1; then
    return 0 
  else
    echo "Invalid date format (YYYY-MM-DD required)."
    exit 1
  fi
}

read -p "Enter start date (YYYY-MM-DD): " start_date
validate_date "$start_date"

read -p "Enter end date (YYYY-MM-DD): " end_date
validate_date "$end_date"

docker build -t call_metrics_image .  
docker run -it --rm --name my-container -v $(pwd):/app call_metrics_image python /app/report_script.py "$start_date" "$end_date"
