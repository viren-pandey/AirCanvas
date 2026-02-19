BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS canvas_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_end TIMESTAMPTZ NULL,
    avg_fps DOUBLE PRECISION NULL
);

CREATE TABLE IF NOT EXISTS saved_frames (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NULL REFERENCES canvas_sessions(id) ON DELETE SET NULL,
    frame_url TEXT NOT NULL,
    thumbnail_url TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    brush_mode VARCHAR(80) NULL,
    shape_mode VARCHAR(80) NULL
);

CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id_start ON canvas_sessions(user_id, session_start DESC);
CREATE INDEX IF NOT EXISTS idx_frames_user_id_created ON saved_frames(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_frames_session_id ON saved_frames(session_id);
CREATE INDEX IF NOT EXISTS idx_frames_shape_mode ON saved_frames(shape_mode);
CREATE INDEX IF NOT EXISTS idx_frames_brush_mode ON saved_frames(brush_mode);

COMMIT;

