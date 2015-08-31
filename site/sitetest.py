from bottle import route, run, view

@route('/home')
@view('landing')
def test():
	return

run(host='localhost', port=8080, debug=True)
