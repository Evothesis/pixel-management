/**
 * User guide and documentation page component.
 * 
 * This component provides comprehensive documentation and guidance for using
 * the pixel management admin interface. It includes setup instructions,
 * feature explanations, troubleshooting tips, and best practices for managing
 * tracking clients and domains.
 * 
 * Key features:
 * - Step-by-step setup and configuration guides
 * - Feature documentation with examples and screenshots
 * - Privacy compliance guidelines for different privacy levels
 * - Domain management and authorization instructions
 * - Troubleshooting section for common issues
 * - API integration examples and code snippets
 * 
 * The user guide serves as comprehensive documentation for admin users
 * and provides context-sensitive help throughout the interface.
 */

// frontend/src/pages/UserGuide.js
import React from 'react';

function UserGuide() {
  const scrollToSection = (sectionId) => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '20px', textAlign: 'left' }}>
      <h1>Pixel Management User Guide</h1>
      <p style={{ fontSize: '1.1em', color: '#666', marginBottom: '30px' }}>
        Complete guide to setting up clients and managing tracking configurations for the Evothesis analytics platform.
      </p>

      {/* Table of Contents */}
      <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '8px', marginBottom: '30px' }}>
        <h3>Quick Navigation</h3>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          <li><button onClick={() => scrollToSection('overview')} style={{ background: 'none', border: 'none', color: '#3182ce', cursor: 'pointer', textDecoration: 'underline' }}>1. Overview</button></li>
          <li><button onClick={() => scrollToSection('adding-client')} style={{ background: 'none', border: 'none', color: '#3182ce', cursor: 'pointer', textDecoration: 'underline' }}>2. Adding a New Client</button></li>
          <li><button onClick={() => scrollToSection('privacy-levels')} style={{ background: 'none', border: 'none', color: '#3182ce', cursor: 'pointer', textDecoration: 'underline' }}>3. Privacy Compliance Levels</button></li>
          <li><button onClick={() => scrollToSection('adding-domains')} style={{ background: 'none', border: 'none', color: '#3182ce', cursor: 'pointer', textDecoration: 'underline' }}>4. Adding Authorized Domains</button></li>
          <li><button onClick={() => scrollToSection('deployment-types')} style={{ background: 'none', border: 'none', color: '#3182ce', cursor: 'pointer', textDecoration: 'underline' }}>5. Deployment Types</button></li>
          <li><button onClick={() => scrollToSection('integration')} style={{ background: 'none', border: 'none', color: '#3182ce', cursor: 'pointer', textDecoration: 'underline' }}>6. Integration with Tracking Infrastructure</button></li>
          <li><button onClick={() => scrollToSection('troubleshooting')} style={{ background: 'none', border: 'none', color: '#3182ce', cursor: 'pointer', textDecoration: 'underline' }}>7. Troubleshooting</button></li>
        </ul>
      </div>

      {/* Overview Section */}
      <section id="overview" style={{ marginBottom: '40px' }}>
        <h2>1. Overview</h2>
        <p>
          The Pixel Management system is the central configuration hub for all Evothesis tracking infrastructure. 
          <strong> Every domain must be explicitly authorized before tracking can begin.</strong> This ensures:
        </p>
        <ul>
          <li>🔒 <strong>Security:</strong> No unauthorized data collection</li>
          <li>⚖️ <strong>Compliance:</strong> Privacy settings enforced automatically</li>
          <li>💰 <strong>Billing:</strong> Only authorized domains generate billable events</li>
          <li>🎯 <strong>Control:</strong> Centralized management of all client configurations</li>
        </ul>

        <div style={{ background: '#fef5e7', border: '1px solid #f6ad55', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#744210' }}>⚠️ Important Security Note</h4>
          <p style={{ margin: 0, color: '#744210' }}>
            Tracking infrastructure will <strong>reject all events</strong> from domains that aren't explicitly authorized in this system. 
            Always add domains to clients before deploying tracking pixels.
          </p>
        </div>
      </section>

      {/* Adding Client Section */}
      <section id="adding-client" style={{ marginBottom: '40px' }}>
        <h2>2. Adding a New Client</h2>
        
        <h3>Step-by-Step Process</h3>
        <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h4>Step 1: Navigate to Client Creation</h4>
          <ol>
            <li>Click <strong>"Add New Client"</strong> from the Dashboard or Client List page</li>
            <li>You'll be taken to the client creation form</li>
          </ol>
        </div>

        <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h4>Step 2: Fill Required Information</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
            <thead>
              <tr style={{ background: '#e2e8f0' }}>
                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #cbd5e0' }}>Field</th>
                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #cbd5e0' }}>Required</th>
                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #cbd5e0' }}>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}><strong>Client Name</strong></td>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>✅ Yes</td>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>Company or organization name</td>
              </tr>
              <tr>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>Email</td>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>❌ No</td>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>Contact email for the client</td>
              </tr>
              <tr>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}><strong>Privacy Level</strong></td>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>✅ Yes</td>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>Compliance level (Standard/GDPR/HIPAA)</td>
              </tr>
              <tr>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}><strong>Deployment Type</strong></td>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>✅ Yes</td>
                <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>Shared infrastructure or dedicated VM</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h4>Step 3: Save and Note Client ID</h4>
          <p>After clicking "Create Client", the system will:</p>
          <ul>
            <li>Generate a unique <code>client_id</code> (e.g., "client_abc123def456")</li>
            <li>Automatically configure privacy settings based on compliance level</li>
            <li>Generate security salts for GDPR/HIPAA clients</li>
          </ul>
          <div style={{ background: '#e6fffa', border: '1px solid #38a169', padding: '10px', borderRadius: '4px', marginTop: '10px' }}>
            <strong>📋 Important:</strong> Save the generated client_id - you'll need it for tracking integration!
          </div>
        </div>
      </section>

      {/* Privacy Levels Section */}
      <section id="privacy-levels" style={{ marginBottom: '40px' }}>
        <h2>3. Privacy Compliance Levels</h2>
        <p>Choose the appropriate privacy level based on your client's requirements and visitor location:</p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginTop: '20px' }}>
          <div style={{ border: '2px solid #38a169', borderRadius: '8px', padding: '20px' }}>
            <h3 style={{ color: '#38a169', marginTop: 0 }}>Standard Level</h3>
            <ul style={{ paddingLeft: '20px' }}>
              <li>Full IP address collection</li>
              <li>All tracking features enabled</li>
              <li>No consent requirements</li>
              <li>Basic PII protection</li>
            </ul>
            <p><strong>Use for:</strong> Internal tools, non-EU visitors, development</p>
          </div>

          <div style={{ border: '2px solid #f6ad55', borderRadius: '8px', padding: '20px' }}>
            <h3 style={{ color: '#744210', marginTop: 0 }}>GDPR Compliant</h3>
            <ul style={{ paddingLeft: '20px' }}>
              <li>IP addresses automatically hashed</li>
              <li>Consent required before tracking</li>
              <li>Aggressive PII redaction</li>
              <li>Do Not Track respect</li>
            </ul>
            <p><strong>Use for:</strong> EU visitors, privacy-conscious clients</p>
          </div>

          <div style={{ border: '2px solid #e53e3e', borderRadius: '8px', padding: '20px' }}>
            <h3 style={{ color: '#822727', marginTop: 0 }}>HIPAA Compliant</h3>
            <ul style={{ paddingLeft: '20px' }}>
              <li>All GDPR features</li>
              <li>Enhanced security measures</li>
              <li>Complete audit logging</li>
              <li>BAA support available</li>
            </ul>
            <p><strong>Use for:</strong> Healthcare organizations, PHI handling</p>
          </div>
        </div>

        <div style={{ background: '#fed7d7', border: '1px solid #e53e3e', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#822727' }}>🚨 Privacy Level Cannot Be Downgraded</h4>
          <p style={{ margin: 0, color: '#822727' }}>
            You can upgrade from Standard → GDPR → HIPAA, but cannot downgrade privacy levels. 
            Choose carefully based on your most restrictive requirement.
          </p>
        </div>
      </section>

      {/* Adding Domains Section */}
      <section id="adding-domains" style={{ marginBottom: '40px' }}>
        <h2>4. Adding Authorized Domains</h2>
        <p>
          <strong>This is the most critical step!</strong> Tracking will not work until domains are explicitly authorized.
        </p>

        <h3>Domain Authorization Process</h3>
        <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h4>Method 1: Via Web Interface (Recommended)</h4>
          <ol>
            <li>Go to <strong>Client List</strong> and click on your client</li>
            <li>Find the <strong>"Domains"</strong> section</li>
            <li>Click <strong>"Add Domain"</strong></li>
            <li>Enter the exact domain (e.g., "example.com")</li>
            <li>Set as primary if this is the main domain</li>
            <li>Click <strong>"Save"</strong></li>
          </ol>
        </div>

        <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h4>Method 2: Via API</h4>
          <pre style={{ background: '#2d3748', color: '#e2e8f0', padding: '15px', borderRadius: '4px', overflow: 'auto' }}>
{`curl -X POST http://localhost:8000/api/v1/admin/clients/{client_id}/domains \\
  -H "Content-Type: application/json" \\
  -d '{
    "domain": "example.com",
    "is_primary": true
  }'`}
          </pre>
        </div>

        <h3>Domain Examples</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '15px' }}>
          <thead>
            <tr style={{ background: '#e2e8f0' }}>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #cbd5e0' }}>✅ Correct Format</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #cbd5e0' }}>❌ Incorrect Format</th>
              <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #cbd5e0' }}>Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>example.com</td>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>https://example.com</td>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>No protocol needed</td>
            </tr>
            <tr>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>www.example.com</td>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>example.com/</td>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>No trailing slash</td>
            </tr>
            <tr>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>app.example.com</td>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>*.example.com</td>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>Each subdomain must be added separately</td>
            </tr>
            <tr>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>localhost</td>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>127.0.0.1</td>
              <td style={{ padding: '12px', border: '1px solid #cbd5e0' }}>Use hostname, not IP</td>
            </tr>
          </tbody>
        </table>

        <div style={{ background: '#fef5e7', border: '1px solid #f6ad55', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#744210' }}>💡 Multiple Domains</h4>
          <p style={{ margin: 0, color: '#744210' }}>
            Clients can have multiple domains. Add each domain separately:
            <br />• Main site: example.com
            <br />• Blog: blog.example.com  
            <br />• App: app.example.com
            <br />• Dev environment: dev.example.com
          </p>
        </div>
      </section>

      {/* Deployment Types Section */}
      <section id="deployment-types" style={{ marginBottom: '40px' }}>
        <h2>5. Deployment Types</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
          <div style={{ border: '2px solid #3182ce', borderRadius: '8px', padding: '20px' }}>
            <h3 style={{ color: '#3182ce', marginTop: 0 }}>Shared Infrastructure</h3>
            <p><strong>Default for most clients</strong></p>
            <ul>
              <li>Cost-effective for smaller clients</li>
              <li>Multiple clients per VM</li>
              <li>Shared resources and scaling</li>
              <li>Standard performance guarantees</li>
            </ul>
            <div style={{ background: '#bee3f8', padding: '10px', borderRadius: '4px', marginTop: '15px' }}>
              <strong>Best for:</strong> &lt;10M events/month, standard privacy requirements
            </div>
          </div>

          <div style={{ border: '2px solid #805ad5', borderRadius: '8px', padding: '20px' }}>
            <h3 style={{ color: '#553c9a', marginTop: 0 }}>Dedicated VM</h3>
            <p><strong>For high-traffic clients</strong></p>
            <ul>
              <li>Isolated infrastructure</li>
              <li>Dedicated resources</li>
              <li>Custom hostname support</li>
              <li>Enhanced performance</li>
            </ul>
            <div style={{ background: '#e9d8fd', padding: '10px', borderRadius: '4px', marginTop: '15px' }}>
              <strong>Best for:</strong> &gt;10M events/month, enterprise clients, HIPAA
            </div>
          </div>
        </div>

        <h3>When to Use Dedicated VM</h3>
        <ul>
          <li>🚀 <strong>High Traffic:</strong> &gt;10M events per month</li>
          <li>🏥 <strong>HIPAA Required:</strong> Healthcare organizations</li>
          <li>🏢 <strong>Enterprise Clients:</strong> Custom branding needs</li>
          <li>⚡ <strong>Performance Critical:</strong> Sub-second response requirements</li>
          <li>🔒 <strong>Data Isolation:</strong> Complete infrastructure separation</li>
        </ul>
      </section>

      {/* Integration Section */}
      <section id="integration" style={{ marginBottom: '40px' }}>
        <h2>6. Integration with Tracking Infrastructure</h2>
        
        <h3>For Shared Infrastructure Clients</h3>
        <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h4>Pixel Endpoint Format</h4>
          <pre style={{ background: '#2d3748', color: '#e2e8f0', padding: '15px', borderRadius: '4px', overflow: 'auto' }}>
{`https://shared.evothesis.com/pixel/{client_id}/tracking.js`}
          </pre>
          <p style={{ marginTop: '10px' }}>Replace <code>{'{client_id}'}</code> with the actual client ID from step 2.</p>
        </div>

        <h3>For Dedicated VM Clients</h3>
        <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h4>Custom Hostname Setup</h4>
          <ol>
            <li>Set the <strong>VM Hostname</strong> field during client creation</li>
            <li>Example: <code>analytics.clientcompany.com</code></li>
            <li>Pixel endpoint becomes: <code>https://analytics.clientcompany.com/pixel/tracking.js</code></li>
          </ol>
        </div>

        <h3>Testing Integration</h3>
        <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h4>Verify Domain Authorization</h4>
          <pre style={{ background: '#2d3748', color: '#e2e8f0', padding: '15px', borderRadius: '4px', overflow: 'auto' }}>
{`# Test domain authorization
curl http://localhost:8000/api/v1/config/domain/example.com

# Should return client configuration, not 404`}
          </pre>
        </div>

        <div style={{ background: '#e6fffa', border: '1px solid #38a169', padding: '15px', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#234e52' }}>✅ Integration Checklist</h4>
          <ul style={{ margin: 0, color: '#234e52' }}>
            <li>Client created with appropriate privacy level</li>
            <li>All domains added and authorized</li>
            <li>Domain authorization tested via API</li>
            <li>Pixel endpoint configured in tracking infrastructure</li>
            <li>Test events successfully collected</li>
          </ul>
        </div>
      </section>

      {/* Troubleshooting Section */}
      <section id="troubleshooting" style={{ marginBottom: '40px' }}>
        <h2>7. Troubleshooting</h2>

        <h3>Common Issues and Solutions</h3>
        
        <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', marginBottom: '20px' }}>
          <h4 style={{ color: '#e53e3e' }}>❌ "Domain not authorized for tracking"</h4>
          <p><strong>Cause:</strong> Domain not added to any client</p>
          <p><strong>Solution:</strong></p>
          <ol>
            <li>Check if domain is spelled correctly</li>
            <li>Verify domain is added to the correct client</li>
            <li>Test: <code>curl http://localhost:8000/api/v1/config/domain/yourdomain.com</code></li>
          </ol>
        </div>

        <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', marginBottom: '20px' }}>
          <h4 style={{ color: '#e53e3e' }}>❌ Tracking pixel not loading</h4>
          <p><strong>Cause:</strong> Incorrect pixel endpoint or client ID</p>
          <p><strong>Solution:</strong></p>
          <ol>
            <li>Verify client_id is correct in pixel URL</li>
            <li>Check tracking infrastructure is pointing to pixel management service</li>
            <li>Test pixel endpoint directly in browser</li>
          </ol>
        </div>

        <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', marginBottom: '20px' }}>
          <h4 style={{ color: '#e53e3e' }}>❌ GDPR/HIPAA compliance not working</h4>
          <p><strong>Cause:</strong> Privacy settings not properly applied</p>
          <p><strong>Solution:</strong></p>
          <ol>
            <li>Verify client privacy level is set correctly</li>
            <li>Check that tracking infrastructure is reading privacy config</li>
            <li>Test IP hashing is working for GDPR/HIPAA clients</li>
          </ol>
        </div>

        <h3>Diagnostic Commands</h3>
        <pre style={{ background: '#2d3748', color: '#e2e8f0', padding: '15px', borderRadius: '4px', overflow: 'auto' }}>
{`# Check client exists and is active
curl http://localhost:8000/api/v1/admin/clients/{client_id}

# Check domain authorization  
curl http://localhost:8000/api/v1/config/domain/{domain}

# List all clients
curl http://localhost:8000/api/v1/admin/clients

# Check client domains
curl http://localhost:8000/api/v1/admin/clients/{client_id}/domains`}
        </pre>

        <h3>Getting Help</h3>
        <div style={{ background: '#bee3f8', border: '1px solid #3182ce', padding: '15px', borderRadius: '8px' }}>
          <p style={{ margin: 0, color: '#1a365d' }}>
            <strong>Need additional support?</strong>
            <br />• Check the API documentation: <a href="/docs" style={{ color: '#3182ce' }}>http://localhost:8000/docs</a>
            <br />• Review system logs: <code>docker compose logs -f</code>
            <br />• Contact the development team with specific error messages
          </p>
        </div>
      </section>

      {/* Quick Reference */}
      <section style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginTop: '40px' }}>
        <h2>Quick Reference</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
          <div>
            <h4>🚀 Getting Started</h4>
            <ol style={{ paddingLeft: '20px' }}>
              <li>Create client</li>
              <li>Set privacy level</li>
              <li>Add domains</li>
              <li>Test authorization</li>
              <li>Deploy tracking</li>
            </ol>
          </div>
          <div>
            <h4>🔧 Key API Endpoints</h4>
            <ul style={{ listStyle: 'none', paddingLeft: 0 }}>
              <li><code>/api/v1/admin/clients</code></li>
              <li><code>/api/v1/config/domain/{'{domain}'}</code></li>
              <li><code>/api/v1/admin/clients/{'{id}'}/domains</code></li>
            </ul>
          </div>
          <div>
            <h4>⚠️ Remember</h4>
            <ul style={{ paddingLeft: '20px' }}>
              <li>Domains must be authorized</li>
              <li>Privacy levels can't be downgraded</li>
              <li>Test before production</li>
              <li>Save client IDs</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

export default UserGuide;