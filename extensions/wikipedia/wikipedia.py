from flask import request
import wikipedia
import urllib.parse

DOMAIN = "wikipedia.org"

def create_search_form():
    return '''
    <center>
    <h1 style="font-family: serif;">Wikipedia<br>The Free Encyclopedia</h1>
    <form action="/wiki/" method="get">
        <input type="text" name="search" required>
        <input type="submit" value="Search">
    </form>
    </center>
    '''

def process_html(content):
    return f'<html><body>{content}</body></html>'

def handle_request(req):
    if req.method == 'GET':
        path = req.path.lstrip('/')
        
        if not path or path == 'wiki/':
            search_query = req.args.get('search', '')
            if not search_query:
                return process_html(create_search_form()), 200
            
            # Redirect to /wiki/[SEARCH_TERM]
            return handle_wiki_page(search_query)

        if path.startswith('wiki/'):
            page_title = urllib.parse.unquote(path.replace('wiki/', ''))
            return handle_wiki_page(page_title)

    return "Method not allowed", 405

def handle_wiki_page(title):
    try:
        page = wikipedia.page(title, auto_suggest=False)
        content = f"<h1>{page.title}</h1>"
        content += page.content
        return process_html(content), 200
    
    except wikipedia.DisambiguationError as e:
        content = f"<h2>{e.title}</h2><p>May refer to:</p><ul>"
        for option in e.options:
            encoded_option = urllib.parse.quote(option)
            content += f'<li><a href="/wiki/{encoded_option}">{option}</a></li>'
        content += "</ul>"
        return process_html(content), 200
    
    except wikipedia.PageError:
        # If the exact page is not found, perform a search
        try:
            search_results = wikipedia.search(title)
            if not search_results:
                return process_html(f"<p>No results found for '{title}'</p>"), 200
            
            content = f"<h2>Search Results for '{title}':</h2><ul>"
            for result in search_results:
                encoded_result = urllib.parse.quote(result)
                content += f'<li><a href="/wiki/{encoded_result}">{result}</a></li>'
            content += "</ul>"
            return process_html(content), 200
        
        except Exception as e:
            return process_html(f"<p>Error: {str(e)}</p>"), 500
    
    except Exception as e:
        return process_html(f"<p>Error: {str(e)}</p>"), 500
