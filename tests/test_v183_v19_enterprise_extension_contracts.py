from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding="utf-8")
def test_v183_control_plane_contracts():
 assert "agent_execution_runs" in read("backend/app/models/control_plane_v183.py"); assert "/control-plane/v18.3" in read("backend/app/api/v1/control_plane_v183.py")
def test_v184_microsoft_contracts():
 s=read("backend/app/api/v1/microsoft_integration_v184.py"); assert "power-automate" in s and "copilot-studio" in s
def test_v185_analytics_contracts():
 s=read("backend/app/api/v1/enterprise_analytics_v185.py"); assert "power-bi" in s and "excel.csv" in s
def test_v19_aws_foundation():
 s=read("infra/aws/__main__.py"); assert "aws.ecs.Cluster" in s and "aws.ecr.Repository" in s and "aws.cloudwatch.LogGroup" in s
def test_ui_surfaces():
 shell=read("frontend/components/control-plane/ControlPlaneShell.tsx"); assert "Run History" in shell and "Microsoft" in shell and "Enterprise BI" in shell
