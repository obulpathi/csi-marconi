import os

from jinja2 import Environment, FileSystemLoader

# once benchmarks are copied, run the perl script for generating the webfiles
# copy benchmarks form each dc into its own folder
# run the benchmarks to generate? .. or later?

# filter the files and rename files
def filter_files():
    pass

# update webpages
def update_website(logs_path):
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

if __name__ == "__main__":
    update_website("/root/logs/")
