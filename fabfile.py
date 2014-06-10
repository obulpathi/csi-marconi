import os
import getpass

from fabric.api import env, run, parallel
from jinja2 import Environment, FileSystemLoader


hosts = ['root@benchmarks-dfw', 'root@benchmarks-ord', 'root@benchmarks-iad',
         'root@benchmarks-lon', 'root@benchmarks-hkg', 'root@benchmarks-syd']


@parallel
def _setup(tenant_id):
    region = env.host[-3:]
    run("apt-get update")
    run("apt-get upgrade -y")
    run("apt-get install -y git")
    run("git clone https://github.com/rackerlabs/csi-marconi.git csi-marconi")
    run("REGION=%s TENANT_ID=%s bash /root/csi-marconi/setup.sh" %
        (region, tenant_id))


def setup():
    tenant_id = raw_input('Enter tenant_id: ')
    env.host = hosts
    _setup(tenant_id)


@parallel
def _benchmark(tenant_id, auth_token):
    region = env.host[-3:]
    run("REGION=%s TENANT_ID=%s AUTH_TOKEN=%s bash /root/csi-marconi/benchmark.sh" %
        (region, tenant_id, auth_token))
    # copy the logs dir to local log server dir
    get("/root/.tsung/log/*", "/root/logs/" + region)
    get("/root/.tsung/log/*", "/usr/share/nginix/html/logs/" + region)


def benchmark():
    tenant_id = raw_input('Enter tenant_id: ')
    auth_token = getpass.getpass('Enter auth_token: ')
    env.host = hosts
    _benchmark(tenant_id, auth_token)

# update webpages
def update_website():
    logs_path = "/usr/share/nginx/html/logs/"
    env = Environment(loader=FileSystemLoader('website/'))
    template = env.get_template('dc.html')
    datacenters = os.listdir(logs_path)
    for datacenter in datacenters:
        benchmarks = os.listdir(logs_path + datacenter)
        latest_benchmarks = sorted(benchmarks)[:10]
        rendered_template = template.render(datacenter = datacenter, benchmarks = benchmarks)
        dc_html = "/root/website/%s.html" % datacenter
        with open(dc_html, "w") as fh:
            fh.write(rendered_template)
        # remove the outdates logs
        outdated_benchmarks = benchmarks[10:]
        for benchmark in outdate_benchmarks:
            os.rmdir(logs_path + datacenter + "/" + benchmark)
