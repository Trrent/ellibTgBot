import aiofiles
from bs4 import BeautifulSoup
import aiohttp

base_url = 'http://flibusta.is/'
search_url = 'http://flibusta.is/booksearch'
book_url = 'http://flibusta.is/b/'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.160 YaBrowser/22.5.1.985 Yowser/2.5 Safari/537.36'}


async def get_books_list(query: str):
    params = {'ask': query}
    async with aiohttp.ClientSession() as session:
        response = await session.get(url=search_url, headers=headers, params=params)
        soup = BeautifulSoup(await response.text(), 'lxml')
        books = []
        chapters = soup.find('div', class_='clear-block', id='main').find_all('h3')
        results = soup.find('div', class_='clear-block', id='main').find_all('ul')
        result = None
        for i in range(len(chapters)):
            if 'Найденные книги' in chapters[i].text:
                result = results[i]
                break
        if not result:
            await session.close()
            return
        for item in result.find_all('li'):
            book_frame, *authors = item.find_all('a')
            book_id = book_frame['href'].split('/')[2]
            book_title = book_frame.text.strip()
            if len(authors) > 1:
                author = ', '.join([i.text.strip() for i in authors])
            else:
                author = authors[0].text.strip()
            books.append({'id': book_id, 'title': book_title, 'author': author})
    return books


async def get_book_info(book_id):
    async with aiohttp.ClientSession() as session:
        response = await session.get(book_url + book_id, headers=headers)
        soup = BeautifulSoup(await response.text(), 'lxml')
        book_title = soup.find('h1', class_='title').text.strip()
        author = soup.find('h1', class_='title').find_next('a').text.strip()
        book_rating = soup.find('div', id='newann')
        if book_rating:
            book_rating = book_rating.text.strip()
        if soup.find('img', title='Cover image'):
            img = base_url[:-1] + soup.find('img', title='Cover image')['src']
        else:
            img = None
        genre = soup.find('p', class_='genre').text.strip()

        description = ' '.join(
            map(lambda x: x.strip(), soup.find('img', title='Cover image').find_next('p').text.split('\n')))
        if not description:
            description = None

        download_links = []
        urls = soup.find_all('a')
        for url in urls:
            for extension in ['fb2', 'epub', 'mobi']:
                if extension in url['href'] and url['href'].startswith('/b'):
                    response = await session.get(base_url[:-1] + url['href'], allow_redirects=True, headers=headers)
                    link = f"{response.real_url.scheme}://{response.real_url.authority}{response.real_url.path_qs}"
                    download_links.append((extension, link))

    return {'id': book_id, 'title': book_title, 'author': author, 'description': description, 'links': download_links,
            'rating': book_rating, 'img': img, 'genre': genre}


async def get_book(url):
    async with aiohttp.ClientSession() as session:
        response = await session.get(url, allow_redirects=True, headers=headers)
        filename = response.content_disposition.filename.replace('.zip', '')
        async with aiofiles.open(filename, 'wb') as f:
            await f.write(await response.content.read())
    return filename
