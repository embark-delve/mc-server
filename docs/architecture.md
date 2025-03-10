# Architecture Overview

The Minecraft Server Manager follows a Service-Oriented Architecture (SOA) with Domain-Driven Design (DDD) principles.

## Architectural Principles

- **Separation of Concerns**: Each component has a single responsibility
- **Interface-Based Design**: All implementations adhere to the same interface
- **Dependency Injection**: Dependencies are injected rather than created
- **Loose Coupling**: Components interact through well-defined interfaces
- **Open/Closed Principle**: Extensible without modifying existing code

## High-Level Architecture

```mermaid
graph TD
    CLI[Command Line Interface] --> MM[Minecraft Manager]
    MM --> SF[Server Factory]
    SF --> |creates| SI[Server Interface]
    SI --> |implemented by| DS[Docker Server]
    SI --> |implemented by| AS[AWS Server]
    SI --> |implemented by| KS[Kubernetes Server]

    DS --> CE[Command Executor]
    AS --> CE
    KS --> CE

    DS --> FM[File Manager]
    AS --> FM
    KS --> FM

    DS --> CO[Console Output]
    AS --> CO
    KS --> CO

    subgraph Utilities
        CE
        FM
        CO
    end

    subgraph Core
        SF
        SI
        MM
    end

    subgraph Implementations
        DS
        AS
        KS
    end
```

## Component Diagram

```mermaid
classDiagram
    class MinecraftServer {
        <<interface>>
        +start() bool
        +stop() bool
        +restart() bool
        +is_running() bool
        +get_status() Dict
        +execute_command(command) str
        +backup() Path
        +restore(backup_path) bool
        +get_logs(lines) List
    }

    class DockerServer {
        -base_dir: Path
        -container_name: str
        -data_dir: Path
        -backup_dir: Path
        -plugins_dir: Path
        -config_dir: Path
        -docker_compose_cmd: List[str]
        +__init__(base_dir, container_name, ...)
        +start() bool
        +stop() bool
        +restart() bool
        +is_running() bool
        +get_status() Dict
        +execute_command(command) str
        +backup() Path
        +restore(backup_path) bool
        +get_logs(lines) List
    }

    class AWSServer {
        -base_dir: Path
        -instance_id: str
        -ssh_key_path: Path
        -ssh_user: str
        -region: str
        -remote_data_dir: str
        -backup_dir: Path
        +__init__(base_dir, instance_id, ...)
        +start() bool
        +stop() bool
        +restart() bool
        +is_running() bool
        +get_status() Dict
        +execute_command(command) str
        +backup() Path
        +restore(backup_path) bool
        +get_logs(lines) List
    }

    class ServerFactory {
        -_implementations: Dict
        +register(server_type, implementation)
        +create(server_type, base_dir, **kwargs) MinecraftServer
        +available_types() List
    }

    class MinecraftManager {
        -base_dir: Path
        -server_type: str
        -server: MinecraftServer
        +__init__(server_type, base_dir, **kwargs)
        +start() bool
        +stop() bool
        +restart() bool
        +backup() Path
        +restore(backup_path) bool
        +get_status() Dict
        +get_logs(lines) List
        +send_command(command) str
    }

    MinecraftServer <|-- DockerServer
    MinecraftServer <|-- AWSServer
    MinecraftManager --> MinecraftServer
    MinecraftManager --> ServerFactory
    ServerFactory --> MinecraftServer
```

## Sequence Diagram: Starting a Server

```mermaid
sequenceDiagram
    actor User
    participant CLI as Command Line Interface
    participant MM as Minecraft Manager
    participant SF as Server Factory
    participant DS as Docker Server
    participant CE as Command Executor

    User->>CLI: ./minecraft-server.py start
    CLI->>MM: main()
    MM->>SF: create("docker", base_dir, **kwargs)
    SF-->>MM: DockerServer instance
    MM->>DS: start()
    DS->>DS: is_running()
    alt Server is already running
        DS-->>MM: True (already running)
        MM-->>CLI: Success message
        CLI-->>User: Server already running
    else Server is not running
        DS->>CE: run(docker-compose up -d)
        CE-->>DS: CompletedProcess
        DS->>DS: Check if server initialized
        DS-->>MM: True/False (started successfully)
        MM-->>CLI: Success/error message
        CLI-->>User: Server started or error
    end
```

## AWS Deployment Architecture

```mermaid
graph TD
    User[User] -->|Interacts with| CLI[CLI Tool]
    CLI -->|Manages| AWS[(AWS Cloud)]

    subgraph AWS Cloud
        EC2[EC2 Instance] -->|Runs| Docker[Docker]
        Docker -->|Runs| MC[Minecraft Server]
        S3[S3 Bucket] -->|Stores| Backups[Backups]
        EC2 -->|Stores data in| EBS[EBS Volume]
        SG[Security Group] -->|Protects| EC2
        ELB[Elastic Load Balancer] -->|Routes to| EC2
    end

    CLI -->|Configures| Terraform[Terraform]
    Terraform -->|Provisions| AWS
```

## Data Flow Diagram

```mermaid
flowchart TD
    User[User] -->|Commands| CLI[CLI Interface]
    CLI -->|Parsed Commands| MM[Minecraft Manager]
    MM -->|Start/Stop/etc.| Server[Server Implementation]

    subgraph Data Flows
        Server -->|Create| Backup[Backup File]
        Backup -->|Restore to| Server
        Server -->|Generate| Logs[Log Data]
        Logs -->|Display to| User
        Server -->|Status| User
        User -->|Server Commands| Server
    end

    subgraph Storage
        Server -->|Read/Write| WorldData[World Data]
        Server -->|Load| Plugins[Plugins]
        Server -->|Use| Config[Configuration]
    end
```

## Plugin Architecture for Extending Server Types

```mermaid
graph LR
    Factory[Server Factory] -->|Creates| Interface[Server Interface]
    Interface -.->|Implemented by| Core[Core Implementations]
    Interface -.->|Implemented by| Plugins[Plugin Implementations]

    subgraph Core Implementations
        Docker[Docker Server]
        AWS[AWS Server]
        K8s[Kubernetes Server]
    end

    subgraph Plugin Implementations
        direction TB
        Custom1[Custom Server Type 1]
        Custom2[Custom Server Type 2]
    end

    Plugin[Plugin Loader] -->|Registers| Plugins
    Plugin -->|With| Factory
```

## Error Handling Flow

```mermaid
flowchart TD
    CLI[CLI Command] --> Handler[Command Handler]
    Handler --> Validation{Input Valid?}

    Validation -->|No| Error1[Validation Error]
    Validation -->|Yes| Execution[Execute Command]

    Execution --> Success{Successful?}
    Success -->|Yes| Result[Return Result]
    Success -->|No| ErrorType{Error Type?}

    ErrorType -->|Connection| NetworkError[Network Error]
    ErrorType -->|Permissions| AuthError[Permission Error]
    ErrorType -->|Server| ServerError[Server Error]

    NetworkError --> Retry{Retry?}
    Retry -->|Yes| Execution
    Retry -->|No| FinalError[Return Error]

    AuthError --> FinalError
    ServerError --> FinalError

    FinalError --> CLI
    Result --> CLI
```

This architecture emphasizes:

1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: New server types can be added without changing core code
3. **Testability**: Clean interfaces make testing straightforward
4. **Maintainability**: Small, focused files with clear domains

For implementation details, see the [API Reference](./api-reference.md).
