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
    webpages_dir = "/usr/share/nginx/html/" + region + "/" + benchmark 
    local_benchmarks_dir  = "/root/logs/" + region + "/" + benchmark
    remote_benchmarks_dir  = "/root/.tsung/log/" + benchmark
    # copy benchmark logs to local logs dir
    get(remote_benchmarks_dir, "/root/logs/" + region)
    # copy the benchmark logs to local temporary directory
    # local("cp -R " + "/root/logs/" + region + "/" + benchmark, "/root/logs/" + region + "/tmp")
    # create a data directory for csv files
    local("mkdir -p " + local_benchmarks_dir + "/csv_data") 
    # generate reports
    local("cd " + local_benchmarks_dir + " && perl ~/csi-marconi/tsung_stats_ng.pl -t ~/csi-marconi/templates")
    local("mkdir -p " + webpages_dir)
    # copy the reports to website directory: /usr/sahre/nginx/html
    local("cp "    + local_benchmarks_dir + "/report.html    " + webpages_dir)
    local("cp "    + local_benchmarks_dir + "/graph.html     " + webpages_dir)
    local("cp -R " + local_benchmarks_dir + "/images         " + webpages_dir)
    local("cp "    + local_benchmarks_dir + "/urlerrors.html " + webpages_dir)
    local("cp -R " + local_benchmarks_dir + "/datas.html     " + webpages_dir)
    local("cp -R " + local_benchmarks_dir + "/data           " + webpages_dir)
    local("cp "    + local_benchmarks_dir + "/tsung.xml      " + webpages_dir)
    local("cd    " + webpages_dir         + " && ln -s ../../static ./static")

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
