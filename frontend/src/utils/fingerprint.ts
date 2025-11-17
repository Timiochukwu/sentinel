/**
 * Device Fingerprinting Utility
 *
 * This module provides device fingerprinting capabilities to detect loan stacking fraud.
 * It uses FingerprintJS to generate a unique, stable identifier for each device based on
 * browser and hardware characteristics.
 *
 * Key Use Cases:
 * 1. Detect multiple users applying from the same device (loan stacking)
 * 2. Detect high-velocity automated fraud attacks
 * 3. Identify devices with fraud history across applications
 * 4. Enable consortium-level device tracking across lenders
 *
 * Privacy Note: This fingerprint is generated from technical characteristics only
 * (screen resolution, canvas rendering, WebGL, etc.) and does not access personal data.
 */

import FingerprintJS from '@fingerprintjs/fingerprintjs'

// Cache the FingerprintJS agent instance to avoid re-initialization
let fpAgent: any = null

/**
 * Initialize the FingerprintJS agent
 * This is called once and the agent is reused for all subsequent fingerprint requests
 *
 * @returns Promise<FingerprintJS.Agent> - The initialized agent
 */
async function initFingerprintAgent() {
  if (!fpAgent) {
    fpAgent = await FingerprintJS.load()
  }
  return fpAgent
}

/**
 * Interface for the complete fingerprint result
 * Contains both the hash and the detailed components used to generate it
 */
export interface DeviceFingerprint {
  // Unique hash representing this device (used for fraud detection queries)
  fingerprint: string

  // Confidence score (0-1) - higher means more stable/reliable fingerprint
  confidence: number

  // Detailed components used to generate the fingerprint
  // Stored for forensics and debugging fraud cases
  components: {
    // Browser and OS information
    userAgent: string
    platform: string
    languages: string[]

    // Hardware characteristics
    screenResolution: string
    availableScreenResolution: string
    colorDepth: number
    hardwareConcurrency: number
    deviceMemory?: number

    // Rendering fingerprints (very stable across sessions)
    canvas?: string
    webgl?: string

    // Time and location settings
    timezone: string
    timezoneOffset: number

    // Additional stability indicators
    sessionStorage: boolean
    localStorage: boolean
    indexedDB: boolean
    cookiesEnabled: boolean

    // Audio fingerprint (if available)
    audio?: string

    // Font detection
    fonts?: string[]
  }

  // Timestamp when fingerprint was generated
  timestamp: number
}

/**
 * Generate a comprehensive device fingerprint
 *
 * This function creates a unique identifier for the current device by analyzing
 * multiple browser and hardware characteristics. The fingerprint is designed to be:
 * - Stable: Persists across sessions and private browsing
 * - Unique: Distinguishes between different devices
 * - Tamper-resistant: Difficult to spoof without sophisticated tools
 *
 * @returns Promise<DeviceFingerprint> - Complete fingerprint object with hash and components
 * @throws Error if fingerprinting fails (e.g., in server-side rendering or bot detection)
 */
export async function getDeviceFingerprint(): Promise<DeviceFingerprint> {
  try {
    // Initialize the FingerprintJS agent
    const agent = await initFingerprintAgent()

    // Get the fingerprint with detailed component information
    const result = await agent.get()

    // Extract key components for storage and analysis
    const components = result.components

    // Build a comprehensive fingerprint object
    const fingerprint: DeviceFingerprint = {
      // The visitorId is the stable hash we use for fraud detection
      fingerprint: result.visitorId,

      // Confidence score (FingerprintJS provides this based on component stability)
      confidence: result.confidence?.score || 0.8,

      // Extract relevant components for forensic analysis
      components: {
        // Browser identification
        userAgent: components.userAgent?.value || navigator.userAgent,
        platform: components.platform?.value || navigator.platform,
        languages: components.languages?.value || navigator.languages || [navigator.language],

        // Screen characteristics (common for loan stacking detection)
        screenResolution: components.screenResolution?.value ||
          `${window.screen.width}x${window.screen.height}`,
        availableScreenResolution: components.availableScreenResolution?.value ||
          `${window.screen.availWidth}x${window.screen.availHeight}`,
        colorDepth: components.colorDepth?.value || window.screen.colorDepth,

        // Hardware capabilities
        hardwareConcurrency: components.hardwareConcurrency?.value || navigator.hardwareConcurrency,
        deviceMemory: (navigator as any).deviceMemory,

        // Canvas fingerprint (very stable, hard to spoof)
        canvas: components.canvas?.value,

        // WebGL fingerprint (GPU-based, extremely stable)
        webgl: components.webglVendorAndRenderer?.value,

        // Timezone information (useful for detecting VPN/location spoofing)
        timezone: components.timezone?.value || Intl.DateTimeFormat().resolvedOptions().timeZone,
        timezoneOffset: new Date().getTimezoneOffset(),

        // Storage availability (bots often have these disabled)
        sessionStorage: components.sessionStorage?.value ?? true,
        localStorage: components.localStorage?.value ?? true,
        indexedDB: components.indexedDb?.value ?? true,
        cookiesEnabled: navigator.cookieEnabled,

        // Audio fingerprint (if available)
        audio: components.audio?.value,

        // Font detection (installed fonts are unique per device)
        fonts: components.fonts?.value
      },

      // Timestamp for tracking when fingerprint was generated
      timestamp: Date.now()
    }

    return fingerprint

  } catch (error) {
    console.error('Failed to generate device fingerprint:', error)

    // Fallback: Generate a basic fingerprint from available browser APIs
    // This ensures we always have some device identifier, even if FingerprintJS fails
    const fallbackFingerprint = generateFallbackFingerprint()

    return {
      fingerprint: fallbackFingerprint,
      confidence: 0.3, // Low confidence for fallback
      components: {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        languages: navigator.languages ? Array.from(navigator.languages) : [navigator.language],
        screenResolution: `${window.screen.width}x${window.screen.height}`,
        availableScreenResolution: `${window.screen.availWidth}x${window.screen.availHeight}`,
        colorDepth: window.screen.colorDepth,
        hardwareConcurrency: navigator.hardwareConcurrency,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        timezoneOffset: new Date().getTimezoneOffset(),
        sessionStorage: true,
        localStorage: true,
        indexedDB: true,
        cookiesEnabled: navigator.cookieEnabled
      },
      timestamp: Date.now()
    }
  }
}

/**
 * Generate a fallback fingerprint using basic browser APIs
 * Used when FingerprintJS fails or is blocked
 *
 * This is less stable and unique than FingerprintJS, but provides a basic
 * device identifier in degraded scenarios (bots, privacy tools, etc.)
 *
 * @returns string - A simple hash of browser characteristics
 */
function generateFallbackFingerprint(): string {
  const characteristics = [
    navigator.userAgent,
    navigator.language,
    navigator.platform,
    window.screen.width,
    window.screen.height,
    window.screen.colorDepth,
    new Date().getTimezoneOffset(),
    navigator.hardwareConcurrency,
    (navigator as any).deviceMemory
  ].join('|')

  // Simple hash function (not cryptographic, just for identifier generation)
  return simpleHash(characteristics)
}

/**
 * Simple hash function for generating fingerprint from string
 * Uses a variation of the DJB2 algorithm
 *
 * @param str - String to hash
 * @returns string - Hexadecimal hash
 */
function simpleHash(str: string): string {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i)
  }
  return Math.abs(hash).toString(16)
}

/**
 * Check if device fingerprinting is available
 * Useful for detecting privacy-focused browsers or bot environments
 *
 * @returns boolean - True if fingerprinting APIs are available
 */
export function isFingerprintingAvailable(): boolean {
  return typeof window !== 'undefined' &&
         typeof navigator !== 'undefined' &&
         typeof document !== 'undefined'
}

/**
 * Validate a fingerprint hash format
 * Fingerprints should be alphanumeric strings of reasonable length
 *
 * @param fingerprint - The fingerprint to validate
 * @returns boolean - True if fingerprint appears valid
 */
export function isValidFingerprint(fingerprint: string): boolean {
  return typeof fingerprint === 'string' &&
         fingerprint.length >= 8 &&
         fingerprint.length <= 128 &&
         /^[a-zA-Z0-9]+$/.test(fingerprint)
}
