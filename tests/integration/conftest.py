from pathlib import Path

import pytest
from indico import IndicoClient, IndicoConfig
from indico.queries import (
    AddModelGroupComponent,
    CreateDataset,
    CreateWorkflow,
    DocumentExtraction,
    GetTrainingModelWithProgress,
    GraphQLRequest,
    JobStatus,
    RetrieveStorageObject,
)

from indico_toolkit.indico_wrapper import DocExtraction, Workflow


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--host",
        required=True,
        help="Specify the host URL for integration tests",
    )
    parser.addoption(
        "--token",
        required=True,
        help="Specify the API token (string or path) for integration tests",
    )


@pytest.fixture(scope="session")
def host(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--host")


@pytest.fixture(scope="session")
def token(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--token")


@pytest.fixture(scope="session")
def indico_client(host: str, token: str) -> IndicoClient:
    if Path(token).is_file():
        return IndicoClient(IndicoConfig(host=host, api_token_path=token))
    else:
        return IndicoClient(IndicoConfig(host=host, api_token=token))


@pytest.fixture(scope="session")
def dataset(indico_client, tests_folder):
    return indico_client.call(
        CreateDataset(
            name="Toolkit Integration Tests",
            files=[tests_folder / "data/samples/fin_disc_snapshot.csv"],
        )
    )


@pytest.fixture(scope="session")
def dataset_id(dataset):
    return dataset.id


@pytest.fixture(scope="session")
def doc_extraction_standard(indico_client):
    return DocExtraction(indico_client)


@pytest.fixture(scope="session")
def extraction_model_group_id(workflow):
    return workflow.components[-1].model_group.id


@pytest.fixture(scope="session")
def extraction_model_id(workflow):
    return workflow.components[-1].model_group.selected_model.id


@pytest.fixture(scope="function")
def function_submission_ids(workflow_id, indico_client, pdf_file):
    workflow_wrapper = Workflow(indico_client)
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, files=[pdf_file])
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    return sub_ids


@pytest.fixture(scope="session")
def model_name(workflow):
    return workflow.components[-1].model_group.name


@pytest.fixture(scope="module")
def module_submission_ids(workflow_id, indico_client, pdf_file):
    workflow_wrapper = Workflow(indico_client)
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, files=[pdf_file])
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    return sub_ids


@pytest.fixture(scope="session")
def ondoc_ocr_object(indico_client, pdf_file):
    job = indico_client.call(
        DocumentExtraction(
            files=[pdf_file], json_config={"preset_config": "ondocument"}
        )
    )
    job = indico_client.call(JobStatus(id=job[0].id, wait=True))
    extracted_data = indico_client.call(RetrieveStorageObject(job.result))
    return extracted_data


@pytest.fixture(scope="session")
def pdf_file(tests_folder: Path) -> Path:
    return tests_folder / "data/samples/fin_disc.pdf"


@pytest.fixture(scope="session")
def populator_snapshot_file(tests_folder: Path) -> Path:
    return tests_folder / "data/snapshots/populator_snapshot.csv"


@pytest.fixture(scope="session")
def standard_ocr_object(indico_client, pdf_file):
    # TODO: this can be static-- probably should be "ondoc" as well
    job = indico_client.call(
        DocumentExtraction(
            files=[pdf_file], json_config={"preset_config": "standard"}
        )
    )
    job = indico_client.call(JobStatus(id=job[0].id, wait=True))
    extracted_data = indico_client.call(RetrieveStorageObject(job.result))
    return extracted_data


@pytest.fixture(scope="session")
def teach_task_id(workflow):
    return workflow.components[-1].model_group.questionnaire_id


@pytest.fixture(scope="module")
def wflow_submission_result(indico_client, module_submission_ids):
    workflow_wrapper = Workflow(indico_client)
    return workflow_wrapper.get_submission_results_from_ids(
        [module_submission_ids[0]],
    )[0]


@pytest.fixture(scope="session")
def workflow(indico_client, dataset):
    workflow = indico_client.call(
        CreateWorkflow(
            dataset.id,
            name="Toolkit Integration Tests",
        )
    )
    workflow = indico_client.call(
        AddModelGroupComponent(
            workflow_id=workflow.id,
            dataset_id=dataset.id,
            name="Toolkit Integration Tests",
            source_column_id=dataset.datacolumn_by_name("text").id,
            labelset_column_id=dataset.labelset_by_name("question_1620").id,
            after_component_id=workflow.components[0].id,
        )
    )

    while True:
        training = indico_client.call(
            GetTrainingModelWithProgress(
                workflow.components[-1].model_group.id
            )
        )

        if training.status not in ("CREATED", "TRAINING"):
            break

    indico_client.call(
        GraphQLRequest(
            """
            mutation AddWorkflowComponent(
                $component: JSONString!
                $workflowId: Int!
                $afterComponentId: Int
            ) {
                addWorkflowComponent(
                    component: $component
                    workflowId: $workflowId
                    afterComponentId: $afterComponentId
                ) {
                    workflow {
                        id
                    }
                }
            }
            """,
            {
                "component": '{"component_type": "default_output", "config": {}}',
                "workflowId": workflow.id,
                "afterComponentId": workflow.components[1].id,
            }
        )
    )

    return workflow


@pytest.fixture(scope="session")
def workflow_id(workflow):
    return workflow.id
