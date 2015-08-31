from bottle import route, run, view

#@route('/hello')
#def hello():
#    return "Hello World!"

@route('/hello')
@view('hello world.html')
def test():
	return
run(host='localhost', port=8080, debug=True)
