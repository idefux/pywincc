import click

@click.command()
@click.argument('src', nargs=-1)
def cc(src):
	print type(src)
	print len(src)
	for s in src:
		print s
        
if __name__ == "__main__":
    cc()