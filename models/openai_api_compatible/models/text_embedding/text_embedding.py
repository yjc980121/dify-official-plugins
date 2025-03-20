from dify_plugin.interfaces.model.openai_compatible.text_embedding import (
    OAICompatEmbeddingModel,
)
from traceback import print_exc

from dify_plugin.errors.model import CredentialsValidateFailedError

class OpenAITextEmbeddingModel(OAICompatEmbeddingModel):
    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials

        :param model: model name
        :param credentials: model credentials
        :return:
        """
        try:
            print("validate_credentials", model, credentials)
            self._invoke(
                model=model,
                credentials=credentials,
                texts=["What is the capital of the United States?"],
                user=None,
            )
        except Exception as ex:
            print_exc()
            raise CredentialsValidateFailedError(str(ex)) from ex
    pass
