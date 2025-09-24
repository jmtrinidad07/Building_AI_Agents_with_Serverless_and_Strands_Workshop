const { Stack } = require('aws-cdk-lib');
const lambda = require('aws-cdk-lib/aws-lambda');
const McpServerConstruct = require('./mcp-server');
const AgentConstruct = require('./agent');
const Cognito = require('./cognito');

// The IaC below uses x86_64 architecture
const FN_ARCHITECTURE = lambda.Architecture.X86_64;
const JWT_SIGNATURE_SECRET = 'jwt-signature-secret';

class StrandsAgentOnLambdaStack extends Stack {
    constructor(scope, id, props) {
        super(scope, id, props);

        const { 
            cognitoJwksUrl 
        } = new Cognito(this, 'Cognito');

        const {
            mcpEndpoint
        } = new McpServerConstruct(this, 'McpServerConstruct',{
            fnArchitecture: FN_ARCHITECTURE,
            jwtSignatureSecret: JWT_SIGNATURE_SECRET
        });

        new AgentConstruct(this, 'AgentConstruct', {
            fnArchitecture: FN_ARCHITECTURE,
            jwtSignatureSecret: JWT_SIGNATURE_SECRET,
            mcpEndpoint,
            cognitoJwksUrl
        });

    }
}

module.exports = { StrandsAgentOnLambdaStack }
