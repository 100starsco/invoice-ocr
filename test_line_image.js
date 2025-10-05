#!/usr/bin/env node
/**
 * Test script to process the LINE chat image directly via OCR service
 * Bypasses LINE API authentication issues and tests enhanced document detection
 */

const axios = require('axios');

async function testLineImageProcessing() {
  console.log('🧪 Testing Enhanced Document Detection with LINE Image');
  console.log('='.repeat(60));

  const ocrServiceUrl = 'http://localhost:8001';

  // Use your LINE image message ID from the logs
  const lineImageId = '580324742130303099';
  const jobId = `test_line_${Date.now()}`;

  // Test data matching your LINE chat image
  const testData = {
    job_id: jobId,
    image_url: `https://obs-us.line-apps.com/r/os/obs/hc/${lineImageId}/original`,
    user_id: 'U092552e6f814223d05ce3719c09424e5', // Your LINE user ID from logs
    message_id: lineImageId,
    webhook_url: 'http://localhost:3000/test-webhook' // Test webhook endpoint
  };

  try {
    console.log(`📤 Submitting OCR job: ${jobId}`);
    console.log(`🖼️  Image URL: ${testData.image_url}`);

    const response = await axios.post(
      `${ocrServiceUrl}/api/v1/jobs/process-invoice`,
      testData,
      {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'dev-ocr-service-key-12345' // Match your .env.dev
        }
      }
    );

    console.log('✅ OCR job submitted successfully!');
    console.log('Job Response:', {
      job_id: response.data.job_id,
      status: response.data.status,
      rq_job_id: response.data.rq_job_id
    });

    // Wait a moment for processing to start
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Check job status
    console.log('\n📊 Checking job status...');
    try {
      const statusResponse = await axios.get(
        `${ocrServiceUrl}/api/v1/jobs/${jobId}/status`
      );

      console.log('Job Status:', statusResponse.data);
    } catch (statusError) {
      console.log('Status check failed (normal during processing):', statusError.response?.data || statusError.message);
    }

    // Check for debug images
    console.log('\n🖼️  Checking for enhanced detection debug images...');
    setTimeout(async () => {
      const { execSync } = require('child_process');

      try {
        // Check if new debug directory was created
        const debugDirs = execSync('ls -lat /tmp/debug_images/ | head -3', { encoding: 'utf8' });
        console.log('Recent debug directories:');
        console.log(debugDirs);

        // Look for the job directory
        const jobDebugPath = `/tmp/debug_images/${jobId}`;
        try {
          const debugFiles = execSync(`ls -la ${jobDebugPath}/ 2>/dev/null || echo "Debug directory not found yet"`, { encoding: 'utf8' });
          console.log(`\nDebug files for ${jobId}:`);
          console.log(debugFiles);
        } catch (e) {
          console.log(`Debug directory ${jobDebugPath} not yet created (processing may still be in progress)`);
        }

      } catch (error) {
        console.log('Error checking debug images:', error.message);
      }
    }, 5000);

    console.log('\n✨ Test completed! Monitor the logs above for enhanced document detection results.');
    console.log('📁 Check /tmp/debug_images/ for visual debug output');
    console.log('🎯 Look for files like: edges_1_conservative.jpg, document_detected_[method].jpg');

  } catch (error) {
    console.error('❌ Test failed:');
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    } else {
      console.error('Error:', error.message);
    }

    // Fallback: Test with a publicly accessible image
    console.log('\n🔄 Trying fallback test with public image...');
    try {
      const fallbackData = {
        ...testData,
        image_url: 'https://httpbin.org/image/jpeg', // Public test image
        job_id: `fallback_${Date.now()}`
      };

      const fallbackResponse = await axios.post(
        `${ocrServiceUrl}/api/v1/jobs/process-invoice`,
        fallbackData,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'dev-ocr-service-key-12345'
          }
        }
      );

      console.log('✅ Fallback test successful:', fallbackResponse.data);

    } catch (fallbackError) {
      console.error('❌ Fallback test also failed:', fallbackError.response?.data || fallbackError.message);
    }
  }
}

// Run the test
testLineImageProcessing().catch(console.error);

module.exports = { testLineImageProcessing };