import sys
import os

# Add vnpy_futu to Python path
vnpy_futu_path = os.path.join(os.path.dirname(__file__), "vnpy_futu")
if vnpy_futu_path not in sys.path:
    sys.path.insert(0, vnpy_futu_path)

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_futu.futu_gateway import FutuGateway
from vnpy_ctabacktester import CtaBacktesterApp


def main():
    """主入口函数"""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(FutuGateway)
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
