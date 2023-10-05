""" import pytest


@pytest.fixture(scope='session') # fixture runs Bot app only once for entire tess session
async def application():
	app = Application.builder().token('<token>' + '/test').build()

	await app.initialize()
	await app.post_init(app) # initialize does *not* call `post_init` - that is only done by run_polling/webhook
	await app.start()
	await app.updater.start_polling()

	yield app

	await app.updater.stop()
	await app.stop()
	await app.shutdown() """