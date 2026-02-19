BEGIN;

ALTER TABLE community_posts
    ADD COLUMN IF NOT EXISTS title VARCHAR(220);

UPDATE community_posts
SET title = LEFT(
    COALESCE(
        NULLIF(TRIM(SPLIT_PART(content, E'\n', 1)), ''),
        'Untitled post'
    ),
    220
)
WHERE title IS NULL OR TRIM(title) = '';

ALTER TABLE community_posts
    ALTER COLUMN title SET DEFAULT 'Untitled post';

ALTER TABLE community_posts
    ALTER COLUMN title SET NOT NULL;

ALTER TABLE community_posts
    ADD COLUMN IF NOT EXISTS score INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_community_posts_score_created
    ON community_posts(score DESC, created_at DESC);

CREATE TABLE IF NOT EXISTS community_post_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vote_value SMALLINT NOT NULL CHECK (vote_value IN (-1, 1)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_post_vote_user UNIQUE (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_community_post_votes_post
    ON community_post_votes(post_id);

CREATE INDEX IF NOT EXISTS idx_community_post_votes_user
    ON community_post_votes(user_id);

CREATE TABLE IF NOT EXISTS community_post_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_comment_id UUID NULL REFERENCES community_post_comments(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_community_post_comments_post_created
    ON community_post_comments(post_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_community_post_comments_user
    ON community_post_comments(user_id);

COMMIT;
