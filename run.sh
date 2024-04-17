function is_valid_date() {
  [[ ! $1 =~ ^[0-9]{4}-[0-1][0-9]{1}-[0-3][0-9]{1}$ ]] && {
    echo "Invalid date format. Please use YYYY-MM-DD."
    exit 1
  }

  [[ $2 -eq 1 ]] && [[ $1 =~ 20[0-9]{2}-(02|([0][4-8]|[1][2-3]))-[0-9]{2} ]] || return 0

  date -d "$1" >/dev/null 2>&1 || {
    echo "Invalid date entered."
    exit 1
  }
}

read -p "Enter start date (YYYY-MM-DD): " start_date
is_valid_date "$start_date"

read -p "Enter end date (YYYY-MM-DD): " end_date
is_valid_date "$end_date"

docker build -t call_metrics_image .  
docker run -it --rm --name my-container -v $(pwd):/app call_metrics_image python /app/report_script.py "$start_date" "$end_date"