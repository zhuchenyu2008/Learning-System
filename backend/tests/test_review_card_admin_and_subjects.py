from sqlalchemy import select

import pytest

from app.models.note import Note
from app.models.review_card import ReviewCard


@pytest.mark.asyncio
async def test_review_card_admin_crud_and_subject_filters(client, session_factory, auth_headers):
    async with session_factory() as session:
        note = Note(
            title='admin-review-note',
            relative_path='notes/generated/admin-review-note.md',
            note_type='source_note',
            content_hash='hash-admin-review-note',
            source_asset_id=None,
            frontmatter_json={'subject': '数学'},
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)

    create_response = await client.post(
        '/api/v1/review/cards/admin',
        json={
            'note_id': note.id,
            'title': '极限定义',
            'content_md': '请解释极限的 epsilon-delta 定义。',
            'summary_text': '当 x 接近某值时，f(x) 接近 L。',
            'tags': ['极限', '定义'],
            'subject': '数学',
            'suspended': False,
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    created = create_response.json()['data']
    assert created['subject'] == '数学'
    assert created['knowledge_point']['title'] == '极限定义'

    subjects_response = await client.get('/api/v1/review/subjects', headers=auth_headers)
    assert subjects_response.status_code == 200
    subjects = subjects_response.json()['data']
    assert any(item['subject'] == '数学' and item['total_cards'] >= 1 for item in subjects)

    admin_list_response = await client.get('/api/v1/review/cards/admin?subject=数学', headers=auth_headers)
    assert admin_list_response.status_code == 200
    listed = admin_list_response.json()['data']
    assert any(item['card_id'] == created['card_id'] for item in listed)

    queue_response = await client.get('/api/v1/review/queue?due_only=false&subject=数学&limit=5', headers=auth_headers)
    assert queue_response.status_code == 200
    queue_items = queue_response.json()['data']
    assert any(item['card_id'] == created['card_id'] for item in queue_items)

    patch_response = await client.patch(
        f"/api/v1/review/cards/admin/{created['card_id']}",
        json={'title': '极限定义（更新）', 'suspended': True, 'subject': '数学'},
        headers=auth_headers,
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()['data']
    assert patched['knowledge_point']['title'] == '极限定义（更新）'
    assert patched['suspended'] is True

    delete_response = await client.delete(f"/api/v1/review/cards/admin/{created['card_id']}", headers=auth_headers)
    assert delete_response.status_code == 200
    deleted = delete_response.json()['data']
    assert deleted['deleted'] is True

    async with session_factory() as session:
        card = (await session.execute(select(ReviewCard).where(ReviewCard.id == created['card_id']))).scalar_one_or_none()
        assert card is None
