clean:
	@rm -f 412alloc *.pyc
	@rm -rf __pycache__

build:
	@echo '#!/bin/bash' > 412alloc
	@echo 'python3 412alloc.py "$$@"' >> 412alloc
	@chmod a+x 412alloc