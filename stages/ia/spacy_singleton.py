import spacy

class SpacyModelSingleton:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = spacy.load("fr_core_news_md")
        return cls._model
