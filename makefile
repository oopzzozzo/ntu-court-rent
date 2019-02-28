.PHONY: all

html=/var/www/html/index.html

$(html): crawl.py
	python3 court_crawl.py > /var/www/html/index.html
