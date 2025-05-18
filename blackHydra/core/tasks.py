from celery import shared_task
import nmap
from .models import ScanResult


@shared_task
def run_port_scan(scan_id):
    scan_obj = ScanResult.objects.get(id=scan_id)
    scan_obj.status = "Scanning"
    scan_obj.save()

    try:
        nm = nmap.PortScanner()
        nm.scan(scan_obj.target, arguments='T4 -F')
        result = nm[scan_obj.target].all_protocols()

        output = ""
        for proto in result:
            ports = nm[scan_obj.target][proto].keys()
            output += f"\nProtocol: {proto.upper()}\n"

            for port in sorted(ports):
                state = nm[scan_obj.target][port]['state']
                output += f"Port {port}: {state}\n"

        scan_obj.status = "completed"
        scan_obj.result = output
        scan_obj.save()

    except Exception as e:
        scan_obj.status = "failed"
        scan_obj.result = str(e)
        scan_obj.save()
        
