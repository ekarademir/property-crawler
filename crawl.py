import urllib.request
import codecs
import re
from datetime import date
from os import listdir

def mop_listing_pages(startURL = "http://www.daft.ie/ireland/houses-for-rent/",
                      count = -1):
    """Save all listing pages to disk

    Keyword Arguments:
    startURL -- Page urllib
    count    -- A count to enumarate saved pages"""


    limit = 10000
    baseurl = u"http://www.daft.ie"
    filehead = u"./data/data-listpage-"
    # Try to load the first page
    try:
        page = urllib.request.urlopen(startURL)
    except Error as err:
        print("Failed at first page:")
        print(format(err))

    # Get the content and search for next link
    # The save the content and then recurse into the next link
    fname = "".join([filehead,
                     str(count+1), u"-",
                     str(date.today().isoformat()),
                     u".dat"])


    content = page.read()

    # Flatten the whole page
    content = content.replace(b'\n', b'\x20').replace(b'\r', b'\x20')
    # Remove some fucking invalid continuation bytes
    invalidbytes = [b'\xe9',
                    b'\xed',
                    b'\xad',
                    b'\x82',
                    b'\x92'
                    ]
    for invalid in invalidbytes:
        content = content.replace(invalid, b'\x00')


    # Finally convert the content into unicode if there is a problem fucking exit
    try:
        content = content.decode('utf-8')
    except UnicodeDecodeError as err:
        print(err)
        return count

    # Check if page has no results
    if None == re.search('<h1>No results</h1>', content):
        f = codecs.open(fname, mode='w', encoding='utf-8')
        f.write(content)
        f.close()
        print("Saved: " + startURL)
        print("\t as " + fname)

        # Get the next page link
        nextpagelink = re.findall('<li\s+class="next_page">.+?</li>', content)

        if len(nextpagelink) > 0:
            # Strip relevant list item
            nextpagelink = nextpagelink[0]
            # Strip href part
            nextpagelink = re.findall('href=".+?"', nextpagelink)[0]
            # Strip link address
            nextpagelink = nextpagelink[6:-1]
            nextpagelink = "".join([baseurl,nextpagelink])

            # Recurse to next page until hitting the limit
            if count + 2 < limit:
                return mop_listing_pages(startURL=nextpagelink, count = count + 1)
            else:
                return count + 2
        else:
            # If no next page link stop
            return count + 2
    else:
        return count + 2

def fetch_listing_pages():
    """Fetches all listing pages and saves to disk."""
    # startURL = u"http://www.daft.ie/ireland/houses-for-rent"
    startURL = u"http://www.daft.ie/ireland/houses-for-rent/?s%5Bignored_agents%5D%5B0%5D=5732&s%5Bignored_agents%5D%5B1%5D=428&s%5Bignored_agents%5D%5B2%5D=1551&offset=1960"
    totalpages = mop_listing_pages(startURL, count = 195)
    print("".join([str(totalpages),
                   u" listing pages saved to disk."]).encode('utf-8'))


def parse_line(line):
    """Parse one line"""

    ############## Getting address line
    address = re.findall('<div class=\"search_result_title_box\">.+?- House', line)[0]
    # Strip anchor
    address = re.findall('\d{6,8}.*House', address)[0]

    # Unique Daft Id
    daftid = re.findall('(\d{6,8}){1}', address)[0]

    address = re.sub('\d{6,8}.*?>', '\x20', address)
    address = re.sub('- House', '\x20', address).strip()

    ############# Getting price and others
    priceline = re.findall('<strong class=\"price\">.+?</strong>', line)[0]
    priceline = re.sub('<.*?strong.*?>', '\x20', priceline)

    # Currency handling
    currencies = {'EUR': '&euro;',
                  'GBP': '&pound;'}
    currency = u"UNK"
    for code, encoded in currencies.items():
        if None != re.search(encoded, priceline):
            priceline = re.sub(encoded, '\x20', priceline)
            currency = code

    priceline = priceline.strip().split(' ')
    # Convert enumeration to proper integer string
    price = str(int(priceline[0].replace(',', '')))
    # Rent period
    rentperiod = " ".join(priceline[1:])
    rentperiod = re.sub('Per ', '', rentperiod)
    # rentperiod = priceline[2]

    ############# Info box
    infoline = re.findall('<ul class=\"info\">.*?</ul>', line)[0]
    infoline = re.sub('<.*?>','',infoline).strip()
    infoline = infoline.split('|')

    housetype = infoline[0].strip()
    bedrooms = infoline[1].strip().split(' ')[0]
    bathrooms = infoline[2].strip().split(' ')[0]

    csvline = ",".join([
        daftid,
        housetype,
        address,
        price,
        currency,
        rentperiod,
        bedrooms,
        bathrooms
    ])
    return csvline

def extract_listings(listingcontent):
    """Extracts apartment listings from given text.

    Arguments:
    listingcontent -- Content of the listing page."""

    listings = re.findall('<div\s+class=\"box\">.+?</li>\s*</ul>\s*</div>\s*</div>\s*',listingcontent)

    listings = [parse_line(x) for x in listings]

    return listings

def save_listings():
    """Fetches all listing in saved listing files and saves
    to a text file."""

    savedlistings = [x
                    for x in listdir('./data')
                    if len(re.findall('listpage', x)) > 0]

    csvfile = u'./data-house-rent-listings.csv'
    csvf = codecs.open(csvfile,'w','utf-8')

    count = 0
    for fname in savedlistings:
        fname = "./data/" + fname
        f = codecs.open(fname, mode='r', encoding='utf-8')
        r = f.readline()
        f.close()
        for listing in extract_listings(r):
            csvf.write(listing + "\n")
            print(listing)
            count += 1
    print(str(count)+" listings recorded")
    csvf.close()

if __name__ == "__main__":
    #fetch_listing_pages()
    save_listings()
