from typing import List, Union

from indico import IndicoClient
from indico.errors import IndicoRequestError
from indico.queries import (
    AddModelGroupComponent,
    CreateStorageURLs,
    GraphQLRequest,
    JobStatus,
    ModelGroupPredict,
    RetrieveStorageObject,
)
from indico.types import Dataset, ModelGroup, Workflow

from ..errors import ToolkitStatusError
from ..retry import retry
from ..types import Predictions


class IndicoWrapper:
    """
    Class for shared API functionality
    """

    def __init__(self, client: IndicoClient):
        """
        Create indico client with user provided arguments

        args:
            client (IndicoClient): instantiated Indico Client object
        """
        self.client = client

    def train_model(
        self,
        dataset: Dataset,
        workflow: Workflow,
        model_name: str,
        source_col: str,
        target_col: str,
        after_component_id: int = None,
    ) -> ModelGroup:
        """
        Train an Indico model
        Args:
            dataset (Dataset): A dataset object (should represent an uploaded CSV
                dataset)
            workflow (Workflow): A workflow object to the corresponding dataset
            model_name (str): the name for your model
            source_col (str): the csv column that contained the text
            target_col (str): the csv column that contained the labels
            after_component_id (int, optional): The workflow component that precedes
                this model group. If None, will be set programmatically to the id of the
                Input OCR Extraction component. Defaults to None.
            wait (bool, optional): Wait for the model to finish training.
                Defaults to False.

        Returns:
            ModelGroup: Model group object
        """
        if not after_component_id:
            after_component_id = workflow.component_by_type("INPUT_OCR_EXTRACTION").id
        return self.client.call(
            AddModelGroupComponent(
                name=model_name,
                dataset_id=dataset.id,
                source_column_id=dataset.datacolumn_by_name(source_col).id,
                labelset_column_id=dataset.labelset_by_name(target_col).id,
                workflow_id=workflow.id,
                after_component_id=after_component_id,
            )
        )

    @retry(IndicoRequestError, ConnectionError)
    def get_storage_object(self, storage_url: str):
        return self.client.call(RetrieveStorageObject(storage_url))

    def create_storage_urls(self, file_paths: List[str]) -> List[str]:
        return self.client.call(CreateStorageURLs(files=file_paths))

    def get_job_status(self, job_id: int, wait: bool = True, timeout: float = None):
        return self.client.call(JobStatus(id=job_id, wait=wait, timeout=timeout))

    @retry(IndicoRequestError, ConnectionError)
    def graphQL_request(self, graphql_query: str, variables: dict = None):
        return self.client.call(
            GraphQLRequest(query=graphql_query, variables=variables)
        )

    def get_predictions_with_model_id(
        self,
        model_id: int,
        samples: List[str],
        load: bool = False,
        options: dict = None,
        wait: bool = True,
    ) -> Union[int, List[Predictions]]:
        """
        Submit samples directly to a model. Note: documents must already be in raw text.
        Args:
            model_id (int): The model ID to submit to
            samples (List[str]): A list containing the text samples you want to submit
            load (bool, optional): [deprecated] Always set to False. Defaults to False.
            options (dict, optional): Model Prediction options. Defaults to None.
            wait (bool, optional): Wait for predictions to finish. Defaults to True.

        Returns: if wait is False, returns the job ID, else returns a list of
            Predictions where each Predictions is either type Classifications or
            Extractions depending on your model.
        """
        job = self.client.call(ModelGroupPredict(model_id, samples, load, options))
        if not wait:
            return job.id
        status = self.get_job_status(job.id, wait=True)
        if status.status != "SUCCESS":
            raise ToolkitStatusError(
                f"Predictions Failed, {status.status}: {status.result}"
            )
        return [Predictions.get_obj(i) for i in status.result]
