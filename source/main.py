from view.titles_view   import TitlesView
from view.historic_view import HistoricView
from view.sidebar_view  import SideBarView

#############################################@
#               View 
#############################################

#Display titles
titles_container = TitlesView(False)
titles_container.build_titles_with_container()

#display historic container 
historic_container = HistoricView(True , 470)
historic_container.build_Historic_Container()

#display the sidebar
sidebar_display = SideBarView()
sidebar_display.display_Logo(True)
sidebar_display.display_Section_Progress()