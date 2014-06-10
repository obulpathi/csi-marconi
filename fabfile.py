import os
import getpass

from fabric.operations import get
from fabric.api import env, run, local, parallel
from jinja2 import Environment, FileSystemLoader

"""
env.hosts = ['root@benchmarks-dfw', 'root@benchmarks-ord', 'root@benchmarks-iad',
             'root@benchmarks-lon', 'root@benchmarks-hkg', 'root@benchmarks-syd']
"""
env.hosts = ['root@benchmarks-hkg']

@parallel
def sample():
    with open(os.path.expanduser("~/.credentials.conf")) as fh:
        credentials = fh.readline().strip()
    tenant_id, auth_token = credentials.split(";")

@parallel
def setup():
    with open(os.path.expanduser("~/.credentials.conf")) as fh:
        credentials = fh.readline().strip()
    tenant_id, _ = credentials.split(";")
    region = env.host_string[-3:]
    run("apt-get update")
    run("apt-get upgrade -y")
    run("apt-get install -y git")
    run("git clone https://github.com/rackerlabs/csi-marconi.git csi-marconi")
    run("REGION=%s TENANT_ID=%s bash /root/csi-marconi/setup.sh" %
        (region, tenant_id))


@parallel
def benchmark():
    with open(os.path.expanduser("~/.credentials.conf")) as fh:
        credentials = fh.readline().strip()
    tenant_id, auth_token = credentials.split(";")
    region = env.host_string[-3:]
    # remove the previous benchmarks, if any
    run("rm -rf /root/.tsung/log/*")
    run("REGION=%s TENANT_ID=%s AUTH_TOKEN=%s bash /root/csi-marconi/benchmark.sh" %
        (region, tenant_id, auth_token))
    # get the benchmarks directory name
    output = run("ls /root/.tsung/log/")
    benchmark = output.stdout
    print(benchmark)
    print(region)
    get("/root/.tsung/log/" + benchmark, "/root/logs/" + region)
    local("mkdir -p /usr/share/nginx/html/" + region + "/" + benchmark)
    local("cp "    + "/root/logs/" + region + "/" + benchmark + "/report.html" + "   " + "/usr/share/nginx/html/" + region + "/" + benchmark + "/report.html")
    local("cp "    + "/root/logs/" + region + "/" + benchmark + "/graph.html"  + "   " + "/usr/share/nginx/html/" + region + "/" + benchmark + "/graph.html")
    local("cp -R " + "/root/logs/" + region + "/" + benchmark + "/images"      + "   " + "/usr/share/nginx/html/" + region + "/" + benchmark)

# update webpages
def update_website():
    website_path = "/usr/share/nginx/html/"
    datacenters = ['hkg']
    jenv = Environment(loader=FileSystemLoader('website/'))
    template = jenv.get_template('dc.html')
    for datacenter in datacenters:
        benchmarks = os.listdir(website_path + datacenter)
        latest_benchmarks = sorted(benchmarks)[:10]
        rendered_template = template.render(datacenter = datacenter, benchmarks = benchmarks)
        dc_html = website_path + datacenter + ".html"
        with open(dc_html, "w") as fh:
            fh.write(rendered_template)
        # remove the outdates logs
        outdated_benchmarks = benchmarks[10:]
        for benchmark in outdated_benchmarks:
            os.remove(website_path + datacenter + "/" + benchmark)
