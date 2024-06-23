document.addEventListener('DOMContentLoaded', (event) => {
  console.log('Client.js loaded');

  const linkButton = document.getElementById('linkButton');
  if (linkButton) {
      linkButton.onclick = function() {
          console.log('Link button clicked');

          fetch('/create_link_token', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  access_token: 'access-production-c8e97de2-bca0-43d0-9ee9-5d18fe3904b2' // Replace with the actual access token
              }),
          })
          .then(response => response.json())
          .then(data => {
              console.log('Link token created:', data);

              const handler = Plaid.create({
                  token: data.link_token, // Use the generated link token
                  onLoad: () => {
                      console.log('Plaid Link loaded');
                  },
                  onSuccess: (public_token, metadata) => {
                      console.log('Plaid link success:', metadata);

                      // Send the public_token to your server
                      fetch('/exchange_public_token', {
                          method: 'POST',
                          headers: {
                              'Content-Type': 'application/json',
                          },
                          body: JSON.stringify({
                              public_token: public_token,
                          }),
                      })
                      .then(response => response.json())
                      .then(data => {
                          console.log('Public token exchanged:', data);
                      })
                      .catch(error => {
                          console.error('Error exchanging public token:', error);
                      });
                  },
                  onExit: (err, metadata) => {
                      console.log('Plaid link exit:', metadata);
                      if (err != null) {
                          // The user encountered a Plaid API error prior to exiting.
                          console.error('Plaid API error:', err);
                      }
                  },
              });

              handler.open();
          })
          .catch(error => {
              console.error('Error creating link token:', error);
          });
      };
  } else {
      console.error('Link button not found');
  }
});
