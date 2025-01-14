import json

class MetaAnalysis(dict):
    """Class representing a Meta-analysis article"""

    __slots__ = (
        "pmid",
        "pmcid",
        "doi",
        "full_text_url",
        "title",
        "abstract",
        "journal",
        "publication_date",
        "figures",
        "supplementary_materials",
        "studies_list"
    )

    def __init__(
        self: object,
        **kwargs: dict,
    ):
        dict.__init__(self, **kwargs)
        for field in self.__slots__:
            self.__setattr__(field, kwargs.get(field, None))

    def set_figures(self: object, figures: list):
        self["figures"] = figures

    def set_supplementary_materials(self: object, supp: list):
        self['supplementary_materials'] = supp

    def set_reference_list(self: object, ref: list):
        self['reference_list'] = ref

    def toJSON(self):
        return json.dumps(self)
    
    def __str__(self: object):
        return self.toJSON()