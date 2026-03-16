-- ============================================================
-- Internship AI Project — Supabase Schema
-- Run this ONCE in Supabase SQL Editor (copy-paste entire file)
-- ============================================================

-- All bot conversation logs (shared table — filtered by bot_id)
CREATE TABLE IF NOT EXISTS conversations (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  bot_id text NOT NULL,           -- 'personal_agent' | 'receptionist' | 'call_center' | 'hotel'
  telegram_user_id text,
  telegram_username text,
  user_message text,
  bot_response text,
  intent text,
  action_taken text,
  created_at timestamptz DEFAULT now()
);

-- Receptionist appointments
CREATE TABLE IF NOT EXISTS appointments (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_name text,
  phone text,
  appointment_datetime text,
  doctor text,
  notes text,
  telegram_user_id text,
  created_at timestamptz DEFAULT now()
);

-- Personal Agent owner instructions (contact → context mapping)
CREATE TABLE IF NOT EXISTS pa_instructions (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  contact_name text,
  contact_context text,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

-- Hotel room bookings
CREATE TABLE IF NOT EXISTS hotel_bookings (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  guest_name text,
  room_type text,
  check_in date,
  check_out date,
  guests_count int DEFAULT 1,
  total_amount decimal,
  telegram_user_id text,
  created_at timestamptz DEFAULT now()
);

-- Hotel food orders
CREATE TABLE IF NOT EXISTS food_orders (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  customer_name text,
  room_number text,
  items jsonb,
  total_amount decimal,
  status text DEFAULT 'pending',
  telegram_user_id text,
  created_at timestamptz DEFAULT now()
);

-- ============================================================
-- Enable Realtime for dashboard live feed
-- ============================================================
ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
ALTER PUBLICATION supabase_realtime ADD TABLE appointments;
ALTER PUBLICATION supabase_realtime ADD TABLE hotel_bookings;
ALTER PUBLICATION supabase_realtime ADD TABLE food_orders;
