import os
import logging
import json
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from typing import Any, Dict, Optional

import httpx
from fastmcp import FastMCP

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TESTING_FARM_API_TOKEN = os.environ.get("TESTING_FARM_API_TOKEN")
TESTING_FARM_API_URL = os.getenv(
    "TESTING_FARM_API_URL", "https://api.testing-farm.io/v0.1"
)
TESTING_FARM_ARTIFACTS_URL = os.getenv(
    "TESTING_FARM_ARTIFACTS_URL", "https://artifacts.dev.testing-farm.io"
)
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

if not TESTING_FARM_API_TOKEN:
    logger.warning("TESTING_FARM_API_TOKEN not set, some operations may fail")

# MCP Server Setup
mcp = FastMCP("Testing-Farm MCP Server")

# Helper Functions
async def fetch_content(url: str) -> Optional[str]:
    """Fetch content from URL"""
    try:
        headers = {}
        if TESTING_FARM_API_TOKEN and "api.testing-farm.io" in url:
            headers["Authorization"] = f"Bearer {TESTING_FARM_API_TOKEN}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {str(e)}")
        return None


async def get_job_status_data(job_id: str) -> Dict[str, Any]:
    """Get job status from API"""
    try:
        url = f"{TESTING_FARM_API_URL}/requests/{job_id}"
        content = await fetch_content(url)
        if content:
            return json.loads(content)
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
    return {}


def extract_failed_tests_from_xml(xml_content: str) -> list:
    """Extract failed test information from XML"""
    try:
        root = ET.fromstring(xml_content)
        failed_tests = []

        for testcase in root.findall(".//testcase"):
            result = testcase.get("result", "unknown")
            if result in ["failed", "error"]:
                test_name = testcase.get("name", "Unknown Test")
                failed_tests.append({
                    "name": test_name,
                    "result": result
                })

        return failed_tests
    except Exception:
        return []


def extract_log_urls_from_xml(xml_content: str) -> list:
    """Extract all log URLs from XML"""
    try:
        root = ET.fromstring(xml_content)
        log_urls = []

        for log_elem in root.findall(".//log"):
            href = log_elem.get("href", "")
            name = log_elem.get("name", "unknown")
            if href.startswith("http"):
                log_urls.append({"name": name, "url": href})

        return log_urls
    except Exception:
        return []


async def find_failure_reason(log_urls: list) -> str:
    """Find failure reason by checking logs"""
    failure_details = []

    # Prioritize certain log types
    priority_logs = []
    other_logs = []

    for log in log_urls:
        name = log["name"].lower()
        if any(keyword in name for keyword in ["output", "failures", "error", "console"]):
            priority_logs.append(log)
        else:
            other_logs.append(log)

    # Check priority logs first, then others
    all_logs = priority_logs + other_logs[:3]  # Limit to avoid too many requests

    for log in all_logs:
        content = await fetch_content(log["url"])
        if content:
            # Look for error patterns in the content
            lines = content.split('\n')
            error_lines = []

            for line in lines:
                line_lower = line.lower().strip()
                if any(keyword in line_lower for keyword in [
                    "error:", "fail", "exception", "traceback", "fatal",
                    "not found", "permission denied", "connection refused",
                    "timeout", "aborted", "killed"
                ]):
                    error_lines.append(line.strip())
                    if len(error_lines) >= 5:  # Limit error lines per log
                        break

            if error_lines:
                failure_details.append(f"From {log['name']}:")
                failure_details.extend([f"  {line}" for line in error_lines])
                failure_details.append("")

    if failure_details:
        return "\n".join(failure_details)
    else:
        return "No specific failure details found in available logs."


# MCP Tools
@mcp.tool()
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get basic status information for a Testing Farm job.

    Args:
        job_id: The job ID of the testing farm run.

    Returns:
        Dict containing job status information.
    """
    try:
        job_data = await get_job_status_data(job_id)

        if not job_data:
            return {"error": f"Could not retrieve job status for {job_id}"}

        return {
            "job_id": job_id,
            "state": job_data.get("state", "unknown"),
            "result": job_data.get("result", {}),
            "created": job_data.get("created"),
            "updated": job_data.get("updated"),
            "environments_requested": job_data.get("environments_requested", [])
        }
    except Exception as e:
        return {"error": f"Error fetching job status: {str(e)}"}


@mcp.tool()
async def analyze_job(job_id: str) -> str:
    """
    Analyze a Testing Farm job - provide summary if successful, find failure reason if failed.

    Args:
        job_id: The job ID of the testing farm run.

    Returns:
        str: Job analysis - either success summary or failure details.
    """
    try:
        # Get job status
        job_data = await get_job_status_data(job_id)

        if not job_data:
            return f"❌ Could not retrieve job data for {job_id}"

        state = job_data.get("state", "unknown")
        result = job_data.get("result", {})

        # Handle running jobs
        if state in ["new", "pending", "running"]:
            return f"⏳ Job {job_id} is still {state}. Please wait for completion."

        # Handle completed jobs
        if state == "complete":
            overall_result = "unknown"
            if isinstance(result, dict):
                overall_result = result.get("overall", "unknown")
            elif isinstance(result, str):
                overall_result = result

            # Success case
            if overall_result in ["passed", "pass", "success"]:
                summary = [
                    f"✅ Job {job_id} completed successfully",
                    f"   State: {state}",
                    f"   Result: {overall_result}",
                    f"   Created: {job_data.get('created', 'unknown')}",
                    f"   Updated: {job_data.get('updated', 'unknown')}"
                ]

                # Add environment info if available
                environments = job_data.get("environments_requested", [])
                if environments:
                    env = environments[0]
                    summary.append(f"   Architecture: {env.get('arch', 'unknown')}")
                    if env.get("os", {}).get("compose"):
                        summary.append(f"   OS: {env['os']['compose']}")

                return "\n".join(summary)

            # Failure case - find the reason
            else:
                analysis = [
                    f"❌ Job {job_id} failed",
                    f"   State: {state}",
                    f"   Result: {overall_result}",
                    f"   Created: {job_data.get('created', 'unknown')}",
                    f"   Updated: {job_data.get('updated', 'unknown')}",
                    "",
                    "🔍 Investigating failure reason..."
                ]

                # Get XML results to find logs
                xml_url = f"{TESTING_FARM_ARTIFACTS_URL}/{job_id}/results.xml"
                xml_content = await fetch_content(xml_url)

                if xml_content:
                    # Extract failed tests
                    failed_tests = extract_failed_tests_from_xml(xml_content)
                    if failed_tests:
                        analysis.append("\n📋 Failed Tests:")
                        for test in failed_tests:
                            analysis.append(f"   • {test['name']}: {test['result']}")

                    # Extract log URLs and find failure reason
                    log_urls = extract_log_urls_from_xml(xml_content)
                    if log_urls:
                        analysis.append(f"\n🔍 Checking {len(log_urls)} available logs...")
                        failure_reason = await find_failure_reason(log_urls)
                        analysis.append("\n💥 Failure Details:")
                        analysis.append(failure_reason)
                    else:
                        analysis.append("\n❓ No detailed logs available for analysis")
                else:
                    analysis.append("\n❓ No XML results available - job may have failed during setup")

                return "\n".join(analysis)

        # Unknown state
        return f"❓ Job {job_id} is in unknown state: {state}"

    except Exception as e:
        return f"❌ Error analyzing job {job_id}: {str(e)}"


# Transport Setup
def main():
    """Main function to run the MCP server"""
    transport = MCP_TRANSPORT.lower()

    if transport == "sse":
        logger.info(f"Starting Testing Farm MCP Server with SSE transport on port {MCP_PORT}")
        mcp.run(transport="sse", port=MCP_PORT)
    else:
        logger.info("Starting Testing Farm MCP Server with stdio transport")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
