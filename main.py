#----------------------------------------
# 核心
#----------------------------------------
import logging
from protractor import Protractor


def main():
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    app = Protractor()
    app.start()
    app.open()


if __name__ == '__main__':
    main()
