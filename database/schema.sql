-- ============================================================================
-- ROIlytics Database Schema (MySQL 8.0 / 9.0+)
-- Database: roilytics_db
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `roilytics_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `roilytics_db`;

-- ----------------------------------------------------------------------------
-- 1. Table: influencers
-- Stores 10,500+ genuine creator profiles with audience & performance metrics
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `influencers` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(100) NOT NULL,
  `full_name` VARCHAR(150) DEFAULT NULL,
  `category` VARCHAR(50) NOT NULL,
  `sub_category` VARCHAR(50) DEFAULT NULL,
  `biography` TEXT DEFAULT NULL,
  `followers_count` BIGINT NOT NULL DEFAULT 0,
  `following_count` INT NOT NULL DEFAULT 0,
  `media_count` INT NOT NULL DEFAULT 0,
  `avg_likes` INT NOT NULL DEFAULT 0,
  `avg_comments` INT NOT NULL DEFAULT 0,
  `avg_video_views` INT NOT NULL DEFAULT 0,
  `engagement_rate` DECIMAL(7, 4) NOT NULL DEFAULT 0.0000,
  `posting_frequency` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
  `estimated_reach` BIGINT NOT NULL DEFAULT 0,
  `is_verified` TINYINT(1) NOT NULL DEFAULT 0,
  `country` VARCHAR(60) NOT NULL DEFAULT 'India',
  `follower_tier` VARCHAR(20) NOT NULL DEFAULT 'Micro',
  `audience_female_pct` DECIMAL(5, 2) DEFAULT 0.50,
  `audience_male_pct` DECIMAL(5, 2) DEFAULT 0.50,
  `audience_age_18_24` DECIMAL(5, 2) DEFAULT 0.35,
  `audience_age_25_34` DECIMAL(5, 2) DEFAULT 0.40,
  `audience_age_35_44` DECIMAL(5, 2) DEFAULT 0.25,
  `spend` DECIMAL(12, 2) DEFAULT 0.00,
  `revenue` DECIMAL(12, 2) DEFAULT 0.00,
  `roi` DECIMAL(8, 4) DEFAULT 0.0000,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY `idx_inf_username` (`username`),
  KEY `idx_inf_cat` (`category`),
  KEY `idx_inf_tier` (`follower_tier`),
  KEY `idx_inf_country` (`country`),
  KEY `idx_inf_er` (`engagement_rate`),
  KEY `idx_inf_followers` (`followers_count`),
  KEY `idx_inf_verified` (`is_verified`),
  KEY `idx_inf_cat_tier` (`category`, `follower_tier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. Table: campaigns
-- Marketing campaigns benchmark data (spend, revenue, impressions, ROI)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `campaigns` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `campaign_id` VARCHAR(50) NOT NULL,
  `brand_name` VARCHAR(100) DEFAULT NULL,
  `category` VARCHAR(50) NOT NULL,
  `platform` VARCHAR(50) NOT NULL DEFAULT 'Instagram',
  `campaign_type` VARCHAR(100) DEFAULT NULL,
  `spend` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  `revenue` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  `roi` DECIMAL(8, 4) NOT NULL DEFAULT 0.0000,
  `impressions` BIGINT NOT NULL DEFAULT 0,
  `reach` BIGINT NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY `idx_cmp_id` (`campaign_id`),
  KEY `idx_cmp_category` (`category`),
  KEY `idx_cmp_roi` (`roi`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. Table: users
-- User accounts for dashboard authentication (local + Google SSO)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(100) NOT NULL,
  `email` VARCHAR(150) NOT NULL,
  `password_hash` VARCHAR(255) DEFAULT NULL,
  `avatar_url` VARCHAR(500) DEFAULT NULL,
  `provider` ENUM('email', 'google') NOT NULL DEFAULT 'email',
  `role` VARCHAR(100) DEFAULT 'Marketing Strategist',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE KEY `idx_usr_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 4. Table: shortlists
-- Saved creator shortlists per user
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `shortlists` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_email` VARCHAR(150) NOT NULL,
  `influencer_id` INT NOT NULL,
  `notes` TEXT DEFAULT NULL,
  `custom_budget` DECIMAL(12, 2) DEFAULT NULL,
  `added_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY `idx_shl_user_inf` (`user_email`, `influencer_id`),
  KEY `idx_shl_user` (`user_email`),
  CONSTRAINT `fk_shortlist_influencer` FOREIGN KEY (`influencer_id`)
    REFERENCES `influencers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 5. Table: roi_predictions
-- Log of ML ROI predictions and budget allocation simulations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `roi_predictions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_email` VARCHAR(150) DEFAULT NULL,
  `category` VARCHAR(50) NOT NULL,
  `followers_count` BIGINT NOT NULL,
  `media_count` INT NOT NULL DEFAULT 0,
  `avg_likes` INT NOT NULL DEFAULT 0,
  `avg_comments` INT NOT NULL DEFAULT 0,
  `spend` DECIMAL(12, 2) NOT NULL,
  `predicted_roi` DECIMAL(8, 4) NOT NULL,
  `predicted_revenue` DECIMAL(12, 2) NOT NULL,
  `predicted_profit` DECIMAL(12, 2) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  KEY `idx_pred_user` (`user_email`),
  KEY `idx_pred_cat` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
