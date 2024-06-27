import json

class MetaAnalysis(dict):
    """Class representing a Meta-analysis article"""

    __slots__ = (
        "pmid",
        "pmcid",
        "doi",
        "title",
        "authors",
        "abstract",
        "journal",
        "publication_date",
        "figures"
    )

    def __init__(
        self: object,
        **kwargs: dict,
    ):
        dict.__init__(self, **kwargs)
        for field in self.__slots__:
            self.__setattr__(field, kwargs.get(field, None))

    def setFigures(self: object, figures: list):
        self["figures"] = figures

    def toJSON(self):
        return json.dumps(self)
    
    def __str__(self: object):
        return self.toJSON()