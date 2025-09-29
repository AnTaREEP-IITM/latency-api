# api/metrics.py
import json
import statistics
import os

def handler(request, response):
    try:
        if request.method != "POST":
            response.status_code = 405
            response.headers["Allow"] = "POST"
            return response

        body = request.get_json()
        regions_req = body.get("regions", [])
        threshold = body.get("threshold_ms", 180)

        # Load dataset bundled with deployment
        data_path = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
        with open(data_path, "r") as f:
            records = json.load(f)

        result = {}

        for region in regions_req:
            region_records = [r for r in records if r["region"] == region]
            if not region_records:
                result[region] = {
                    "avg_latency": None,
                    "p95_latency": None,
                    "avg_uptime": None,
                    "breaches": None,
                }
                continue

            latencies = [r["latency_ms"] for r in region_records]
            uptimes = [r["uptime_pct"] for r in region_records]

            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=100)[94]  # 95th percentile
            avg_uptime = statistics.mean(uptimes)
            breaches = sum(1 for x in latencies if x > threshold)

            result[region] = {
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "avg_uptime": avg_uptime,
                "breaches": breaches,
            }

        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Content-Type"] = "application/json"
        response.write(json.dumps(result))
        return response

    except Exception as e:
        response.status_code = 400
        response.headers["Content-Type"] = "application/json"
        response.write(json.dumps({"error": str(e)}))
        return response
