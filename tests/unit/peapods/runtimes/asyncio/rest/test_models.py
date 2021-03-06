from tests import random_docs
from jina.peapods.runtimes.asyncio.rest.models import PROTO_TO_PYDANTIC_MODELS


def test_schema_invocation():
    for k, v in PROTO_TO_PYDANTIC_MODELS.items():
        v.schema()
        v.schema_json()


def test_existing_definitions():
    """ This tests: all internal schema definitions are part of parent """
    for i in [
        'QuantizationMode',
        'DenseNdArrayProto',
        'SparseNdArrayProto',
        'NdArrayProto',
        'NamedScoreProto',
        'DocumentProto',
    ]:
        assert (
            i
            in PROTO_TO_PYDANTIC_MODELS['DocumentProto']()
            .schema()['definitions']
            .keys()
        )


def test_enum_definitions():
    """ This tests: all enums are defined properly as different levels """
    quantization_enum_definition = PROTO_TO_PYDANTIC_MODELS['DocumentProto']().schema()[
        'definitions'
    ]['QuantizationMode']
    assert quantization_enum_definition['enum'] == [0, 1, 2]

    status_code_enum_definition = PROTO_TO_PYDANTIC_MODELS['StatusProto']().schema()[
        'definitions'
    ]['StatusCode']
    assert status_code_enum_definition['enum'] == [0, 1, 2, 3, 4, 5, 6]

    command_enum_definition = PROTO_TO_PYDANTIC_MODELS['RequestProto']().schema()[
        'definitions'
    ]['Command']
    assert command_enum_definition['enum'] == [0, 1, 3]


def test_all_fields_in_document_proto():
    """ This tests: all fields are picked from the proto definition """
    document_proto_properties = PROTO_TO_PYDANTIC_MODELS['DocumentProto']().schema(
        by_alias=False
    )['definitions']['DocumentProto']['properties']
    for i in [
        'id',
        'content_hash',
        'granularity',
        'adjacency',
        'level_name',
        'parent_id',
        'content',
        'chunks',
        'weight',
        'length',
        'matches',
        'mime_type',
        'uri',
        'tags',
        'location',
        'offset',
        'embedding',
        'score',
        'modality',
        'evaluations',
    ]:
        assert i in document_proto_properties

    document_proto_properties_alias = PROTO_TO_PYDANTIC_MODELS[
        'DocumentProto'
    ]().schema()['definitions']['DocumentProto']['properties']
    for i in ['contentHash', 'levelName', 'parentId', 'mimeType']:
        assert i in document_proto_properties_alias


def test_oneof():
    """ This tests: oneof field is correctly represented as `anyOf` """
    content = PROTO_TO_PYDANTIC_MODELS['DocumentProto']().schema()['definitions'][
        'DocumentProto'
    ]['properties']['content']
    assert 'anyOf' in content
    assert len(content['anyOf']) == 3
    assert {'$ref': '#/definitions/NdArrayProto'} in content['anyOf']

    body = PROTO_TO_PYDANTIC_MODELS['RequestProto']().schema()['properties']['body']
    assert 'anyOf' in body
    assert len(body['anyOf']) == 6
    assert {'$ref': '#/definitions/IndexRequestProto'} in body['anyOf']
    assert {'$ref': '#/definitions/TrainRequestProto'} in body['anyOf']


def test_repeated():
    """ This tests: repeated fields are represented as `array` """
    assert (
        PROTO_TO_PYDANTIC_MODELS['DenseNdArrayProto']().schema()['properties']['shape'][
            'type'
        ]
        == 'array'
    )
    assert (
        PROTO_TO_PYDANTIC_MODELS['NamedScoreProto']().schema()['definitions'][
            'NamedScoreProto'
        ]['properties']['operands']['type']
        == 'array'
    )
    assert (
        PROTO_TO_PYDANTIC_MODELS['DocumentProto']().schema()['definitions'][
            'DocumentProto'
        ]['properties']['chunks']['type']
        == 'array'
    )


def test_recursive_schema():
    """ This tests: recursive schmea definions are represented properly """
    assert PROTO_TO_PYDANTIC_MODELS['NamedScoreProto']().schema()['definitions'][
        'NamedScoreProto'
    ]['properties']['operands']['items'] == {'$ref': '#/definitions/NamedScoreProto'}


def test_struct():
    """ This tests: google.protobuf.Struct are represented as `object` """
    assert (
        PROTO_TO_PYDANTIC_MODELS['DocumentProto']().schema()['definitions'][
            'DocumentProto'
        ]['properties']['tags']['type']
        == 'object'
    )


def test_timestamp():
    """ This tests: google.protobuf.Timestamp are represented as date-time """
    assert (
        PROTO_TO_PYDANTIC_MODELS['RouteProto']().schema(by_alias=False)['properties'][
            'start_time'
        ]['type']
        == 'string'
    )
    assert (
        PROTO_TO_PYDANTIC_MODELS['RouteProto']().schema(by_alias=False)['properties'][
            'start_time'
        ]['format']
        == 'date-time'
    )


def test_jina_document_to_pydantic_document():
    document_proto_model = PROTO_TO_PYDANTIC_MODELS['DocumentProto']

    for jina_doc in random_docs(num_docs=10):
        jina_doc = jina_doc.dict()
        pydantic_doc = document_proto_model(**jina_doc)

        assert jina_doc['text'] == pydantic_doc.text
        assert jina_doc['mimeType'] == pydantic_doc.mime_type
        assert jina_doc['contentHash'] == pydantic_doc.content_hash
        assert (
            jina_doc['embedding']['dense']['shape']
            == pydantic_doc.embedding.dense.shape
        )
        assert (
            jina_doc['embedding']['dense']['dtype']
            == pydantic_doc.embedding.dense.dtype
        )

        for jina_doc_chunk, pydantic_doc_chunk in zip(
            jina_doc['chunks'], pydantic_doc.chunks
        ):
            assert jina_doc_chunk['id'] == pydantic_doc_chunk.id
            assert jina_doc_chunk['tags'] == pydantic_doc_chunk.tags
            assert jina_doc_chunk['text'] == pydantic_doc_chunk.text
            assert jina_doc_chunk['mimeType'] == pydantic_doc_chunk.mime_type
            assert jina_doc_chunk['parentId'] == pydantic_doc_chunk.parent_id
            assert jina_doc_chunk['granularity'] == pydantic_doc_chunk.granularity
            assert jina_doc_chunk['contentHash'] == pydantic_doc_chunk.content_hash
