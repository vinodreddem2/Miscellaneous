from bs4 import BeautifulSoup
row = "<tr><th>Header 1</th><th>Header 2</th><td>Data 1</td><td>Data 2</td></tr>"
soup = BeautifulSoup(row, 'html.parser')
cells = row.find_all(['td', 'th'])
print(cells)
print(len(cells))