# Generates html table of renting records
import requests, json
import datetime
from dateutil.relativedelta import relativedelta
import re
import os

crawltime = datetime.datetime.now()
month = (crawltime+relativedelta(months=+1)).strftime('%Y-%m')
dom = (crawltime+relativedelta(months=+2)+relativedelta(day=1)+relativedelta(days=-1)).strftime('%d')

url_off = 'https://pe.ntu.edu.tw/api/rent/activityused?sdate='+month+'-01'+'&edate='+month+'-'+dom
url_peer = 'https://pe.ntu.edu.tw/api/rent/yearuserrent?rentDateS='+month+'-01'+'&rentDateE='+month+'-'+dom

# place to dump ontained json
dumpdir = '/var/www/html/court/history/'
dumpfn = '-rent.json'

# modify here
minded_court = ['中央籃球場(1)', '中央籃球場(2)', '中央籃球場(3)', '新生籃球場(I)', '新生籃球場(II)', '新生籃球場(III)女生', '籃球場甲(A)', '籃球場乙(B)', '籃球場丙(C)', '籃球場丁(D)', '籃球場戊(E)']
minded_day = [1, 3] # Mon=0 Tue=1 ...
timep = ["18:00~20:00", "20:00~22:00"]
our_names = ['資訊工程所女', '資訊工程系女']

date_type = lambda x: datetime.datetime.strptime(x.split()[0],'%Y-%m-%d')
care_day = lambda x: (date_type(x).weekday() in minded_day)
dates = list(filter(care_day, [month+'-{:02d} 00:00:00'.format(d) for d in range(1,int(dom)+1)]))
def care_peer(x):
  return (x['venueName'] in minded_court) and (x['rentDate'] in dates) and (x['rentTimePeriod'] in timep)
def care_off(x):
  return (x['venueName'] in minded_court) and filter(lambda d: (d+6)%7 in minded_day, x['activityWeek']) != []
def drawn(x):
  return (x['statusDraw'] == 1)
def not_drawn(x):
  return (x['statusDraw'] == 2)

# request and dump filtered json
content_peer = list(filter(care_peer, json.loads(requests.get(url_peer).text)))
content_off = list(filter(care_off, json.loads(requests.get(url_off).text)))
with open(dumpdir+month+dumpfn, "w") as fp:
  json.dump(content_peer, fp)
  json.dump(content_off, fp)

# shorten, highlight and bucket to cells
shorten_tips = {
    ' ':'',
    '\d+':'',
    '學?系?(研究)?所':'所',
    '子?籃球隊':'',
    '(..)科?學系': (lambda m: m.group(1)+'系'),
    }
def shorten(s, strong, weak):
  for k, v in shorten_tips.items():
    s = re.sub(k, v, s)
  s =  re.sub('(..)..(..).*(..)', lambda m: m.group(1)+m.group(2)+m.group(3), s)
  if s in our_names:
    s = '<ours>' + s + '</ours>'
  elif s[-1] == '女':
    s = '<girl>' + s + '</girl>'
  elif s[-1] == '男':
    s = '<boy>' + s + '</boy>' 
  if strong:
    return '<strong>'+s+'</strong>'
  elif weak:
    return '<weak>'+s+'</weak>'
  else:
    return '<truth>'+s+'</truth>'

display = {(d+t):{vn:[] for vn in minded_court} for t in timep for d in dates}
for r in content_peer:
    display[r['rentDate']+r['rentTimePeriod']][r['venueName']].append(shorten(r['yearUserUnitName'], drawn(r), not_drawn(r)) + '<br>')
for r in content_off:
  for d, dd in zip(dates, map(date_type,dates)):
    if date_type(r['beginDate']) <= dd <= date_type(r['endDate']) and ((dd.weekday()+1)%7 in r['activityWeek']):
      for t in set(r['timePeriod']) & set(timep):
        display[d+t][r['venueName']].append('<strong>' + r['activityName'][0:6] + '</strong><br>')

#display
trow = lambda h,X:'<tr><td>'+h+'</td>'.join(['<td>'+x+'</td>' for x in X])+'</tr>'
list_departments = lambda l:''.join(sorted(l, key=lambda s:s[::-1]))

print('<html><head><meta charset="UTF-8"><link rel="stylesheet" href="style/court.css"><title>court!</title></head>')
print('<body>Last update: '+str(crawltime))
print('<table border=1>'+trow('',minded_court))
week = ["(一)","(二)","(三)","(四)","(五)","(六)","(日)"]
for d in dates:
  for t in timep:
    dd = datetime.datetime.strptime(d.split()[0],'%Y-%m-%d')
    print(trow(d.split()[0]+' '+week[dd.weekday()]+'<br>'+t, map(lambda x:list_departments(display[d+t][x]), minded_court)))
print('</table></body></html>')
