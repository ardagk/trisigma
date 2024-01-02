from dataclasses import dataclass
from trisigma.domain.common import modelfactory

@dataclass(frozen=True)
class Instrument:
    family: str
    base: str
    quote: str

    @staticmethod
    def parse(instrument: str):
        if instrument.count("_") == 2:
            family, base, quote = tuple(instrument.split("_"))
            return Instrument(family, base, quote)
        elif (instrument.count("_") == 0
              and instrument.count("/") == 1
              and instrument.count(":") == 1):
            family, base_quote = tuple(instrument.split(":"))
            base, quote = tuple(base_quote.split("/"))
            return Instrument(family, base, quote)
        else:
            raise ValueError(
                "Instrument parsing error: {}, \
                (format: [family]:[base]/[quote])".format(instrument))

    @staticmethod
    def crypto(base: str, quote: str):
        return Instrument("crypto", base, quote)

    @staticmethod
    def stock(base: str, quote: str):
        return Instrument("stock", base, quote)

    def __str__(self):
        return f"{self.family}:{self.base}/{self.quote}"
