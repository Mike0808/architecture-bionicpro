import React from 'react';
import { ReactKeycloakProvider } from '@react-keycloak/web';
import Keycloak, { KeycloakConfig } from 'keycloak-js';
import ReportPage from './components/ReportPage';

// interface KeycloakConfigWithPKCE extends KeycloakConfig {
//   pkceMethod?: 'S256';
// }
// const keycloakConfig: KeycloakConfigWithPKCE = {
//   url: process.env.REACT_APP_KEYCLOAK_URL,
//   realm: process.env.REACT_APP_KEYCLOAK_REALM||"",
//   clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID||"",
//   pkceMethod: 'S256'
// };

const keycloak = new Keycloak({
  url: process.env.REACT_APP_KEYCLOAK_URL,
  realm: process.env.REACT_APP_KEYCLOAK_REALM || '',
  clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID || '',
  pkceMethod: 'S256'
} as any);

const App: React.FC = () => {
  return (
    <ReactKeycloakProvider authClient={keycloak}
        initOptions={{
        onLoad: 'check-sso', // Проверяет сессию при загрузке
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        pkceMethod: 'S256' // ← Вот где нужно указать PKCE!
      }}
    >
      <div className="App">
        <ReportPage />
      </div>
    </ReactKeycloakProvider>
  );
};

export default App;