# -*- coding: utf-8 -*-
import html5

from vi.network import NetworkService, DeferredCall
from vi.i18n import translate
from vi.config import conf
from vi.widgets.task import TaskSelectWidget
from vi.priorityqueue import toplevelActionSelector
from vi.widgets.button import Button
from vi.embedsvg import embedsvg
from vi.pane import Pane
from vi.widgets.edit import EditWidget

class TopBarWidget(html5.Header):
	"""
		Provides the top-bar of VI
	"""
	def __init__(self):
		super(TopBarWidget,self ).__init__()

		self["class"] = "vi-topbar bar"

		self.sinkEvent("onClick")

		self.fromHTML("""
			<div class="vi-tb-left bar-group bar-group--left" [name]="topbarLeft">
				<div class="vi-tb-logo" [name]="topbarLogo"></div>
				<h1 class="vi-tb-title" [name]="moduleH1"></h1>
				<div class="vi-tb-currentmodul item" [name]="moduleContainer">
					<div class="item-image" [name]="modulImg"></div>
					<div class="item-content" [name]="moduleName"></div>
				</div>
			</div>
			<nav class="vi-tb-right bar-group bar-group--right" [name]="topbarRight">
				<div class="input-group" [name]="iconnav">
				</div>
			</nav>
		""")

		svg = embedsvg.get("logos-vi")
		if svg:
			self.topbarLogo.element.innerHTML = svg + self.topbarLogo.element.innerHTML

		DeferredCall(self.setTitle, _delay=500)

	def invoke(self):
		self.iconnav.removeAllChildren()

		newBtn = html5.A()
		newBtn["href"] = "https://www.viur.is"
		newBtn["target"] = "_blank"
		newBtn.addClass("btn")
		svg = embedsvg.get("icons-ribbon")
		if svg:
			newBtn.element.innerHTML = svg + newBtn.element.innerHTML
		newBtn.appendChild(translate("vi.topbar.newbtn"))
		#self.iconnav.appendChild(newBtn)

		newMarker = html5.Span()
		newMarker.addClass("marker")
		newMarker.appendChild(translate("vi.topbar.new"))
		newBtn.appendChild(newMarker)

		for icon in conf["toplevelactions"]:
			widget = toplevelActionSelector.select(icon)
			if widget:
				self.iconnav.appendChild(widget())

	def setTitle(self, title=None):
		self.moduleH1.removeAllChildren()

		if title is None:
			title = conf.get("vi.name")

		if title:
			self.moduleH1.appendChild(html5.TextNode(html5.utils.unescape(title)))

	def onClick(self, event):
		if html5.utils.doesEventHitWidgetOrChildren(event, self.moduleH1):
			conf["mainWindow"].switchFullscreen(not conf["mainWindow"].isFullscreen())

	def setCurrentModulDescr(self, descr = "", iconURL=None, iconClasses=None, path=None):
		for c in self.modulImg._children[:]:
			self.modulImg.removeChild(c)
		for c in self.moduleName._children[:]:
			self.moduleName.removeChild( c )
		for c in self.modulImg["class"]:
			self.modulImg.removeClass(c)

		self.modulImg.addClass("item-image")

		descr = html5.utils.unescape(descr)
		self.moduleName.appendChild(html5.TextNode(descr))

		if iconURL is not None:
			svg = embedsvg.get(iconURL)
			if svg:
				modulIcon = html5.I()
				modulIcon.addClass("i")
				modulIcon.element.innerHTML = svg + modulIcon.element.innerHTML
				self.modulImg.appendChild(modulIcon)
			else:
				img = html5.Img()
				img["src"] = iconURL
				self.modulImg.appendChild(img)

		if iconClasses is not None:
			for cls in iconClasses:
				self.modulImg.addClass( cls )

		conf["theApp"].setTitle(descr)

		if path:
			conf[ "theApp" ].setPath( path )

class UserState(Button):
	def __init__(self, *args, **kwargs):
		super( UserState, self ).__init__(*args, **kwargs)
		self.sinkEvent( "onClick" )
		self.update()

	def onCurrentUserAvailable(self, req):
		data = NetworkService.decode( req )
		conf[ "currentUser" ] = data[ "values" ]
		self.update()

	def update(self):
		user = conf.get( "currentUser" )
		if not user:
			NetworkService.request( "user", "view/self",
			                        successHandler=self.onCurrentUserAvailable,
			                        cacheable=False )
			return

		self["title"] = user["name"]
		self.currentUser = user["key"] or None
		self.addClass("vi-tb-accountmgnt")
		self.appendChild(html5.TextNode(user["name"]))

	@staticmethod
	def canHandle( action ):
		return action == "userstate"

	def onClick( self, sender=None ):
		#load user module if not already loaded
		if not "user" in conf["modules"].keys():
			conf["modules"].update(
				{"user": {"handler": "list",
			              "name": "Benutzer"}
			    })

		self.openEdit( self.currentUser )

	def openEdit(self, key):
		apane = Pane(
			translate("Edit"),
			closeable=True,
			iconClasses=["module_%s" % "user", "apptype_list", "action_edit"],
			collapseable=True
		)

		conf["mainWindow"].addPane(apane)
		edwg = EditWidget("user", EditWidget.appList, key=key)

		actions = edwg.actionbar.getActions()
		actions.append("cancel.close")
		edwg.actionbar.setActions(actions)

		apane.addWidget(edwg)

		conf["mainWindow"].focusPane(apane)


toplevelActionSelector.insert( 0, UserState.canHandle, UserState )


class Tasks(Button):
	def __init__(self, *args, **kwargs):
		super(Tasks, self).__init__(icon="icons-settings", *args, **kwargs)
		self.sinkEvent("onClick")
		self.hide()
		self.addClass("btn vi-tb-tasks")
		self.appendChild(html5.TextNode(translate("vi.tasks")))

		if not conf[ "tasks" ][ "server" ]:
			NetworkService.request( None, "/vi/_tasks/list",
		        successHandler=self.onTaskListAvailable,
		        cacheable=False )

		self.update()

	def onTaskListAvailable(self, req):
		data = NetworkService.decode(req)
		if not "skellist" in data.keys() or not data[ "skellist" ]:
			conf[ "tasks" ][ "server" ] = []
			self.hide()
			return

		conf[ "tasks" ][ "server" ] = data[ "skellist" ]

	def onTaskListFailure(self):
		self.hide()

	def onCurrentUserAvailable(self, req):
		data = NetworkService.decode( req )
		conf[ "currentUser" ] = data[ "values" ]
		self.update()

	def update(self):
		user = conf.get( "currentUser" )
		if not user:
			NetworkService.request( "user", "view/self",
			                        successHandler=self.onCurrentUserAvailable,
			                        cacheable=False )
			return

		if "root" in user[ "access" ]:
			self.show()

	def onClick(self, event ):
		TaskSelectWidget()

	@staticmethod
	def canHandle( action ):
		return action == "tasks"

toplevelActionSelector.insert( 0, Tasks.canHandle, Tasks )


class Logout(Button):
	def __init__(self, *args, **kwargs):
		super(Logout,self).__init__(icon="icons-logout", *args, **kwargs)
		self.addClass("btn vi-tb-logout")
		self.appendChild(html5.TextNode(translate("Logout")))
		self.sinkEvent("onClick")

	def onClick(self, event):
		html5.ext.YesNoDialog( translate(u"Möchten Sie das Vi wirklich beenden?\n Alle nicht gespeicherten Einträge gehen dabei verloren!"), title = u"Logout", yesCallback = self.logout )
		event.stopPropagation()
		event.preventDefault()

	def logout( self ):
		conf[ "theApp" ].logout()

	@staticmethod
	def canHandle( action ):
		return action == "logout"

toplevelActionSelector.insert( 0, Logout.canHandle, Logout )

#FIXME: Put Message Center in Iconnav. The message center will be a popout in the topbar.
