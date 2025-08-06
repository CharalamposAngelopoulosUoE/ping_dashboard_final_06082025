# Stop and remove all containers
docker ps -aq | ForEach-Object { docker stop $_; docker rm $_ }

# Remove old images
docker images ping_dashboard -q | ForEach-Object { docker rmi -f $_ }

# Navigate to project folder
cd "C:\Users\cangelop\Documents\GitHub\ping_dashboard_final_06082025"

# Build fresh image
docker build --no-cache -t ping_dashboard .

# Run with volume mount for Excel
docker run -p 5000:5000 -v ${PWD}/data/IP_List.xlsx:/app/data/IP_List.xlsx ping_dashboard
