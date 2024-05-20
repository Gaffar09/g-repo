const { defineConfig } = require('cypress')
const {downloadFile} = require('cypress-downloadfile/lib/addPlugin')

module.exports = defineConfig({
  projectId: 'dqgac3',
  // setupNodeEvents can be defined in either
  // the e2e or component configuration
  e2e: {
    setupNodeEvents(on, config) {
         on('task', {downloadFile})
      }
    }
  }
)
{
  "reporter"; "mochawesome",
  "reporterOptions"; {
    "charts"; true,
    "overwrite"; false,
    "html"; false,
    "json"; true,
    "reportDir"; "cypress/report/mochawesome-report"
   }
  }
 

