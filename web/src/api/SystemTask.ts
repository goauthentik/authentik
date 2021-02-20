import { DefaultClient, QueryArguments } from "./Client";

export enum TaskStatus {
    SUCCESSFUL = 1,
    WARNING = 2,
    ERROR = 4,
}

export class SystemTask {

    task_name: string;
    task_description: string;
    task_finish_timestamp: number;
    status: TaskStatus;
    messages: string[];

    constructor() {
        throw Error();
    }

    static get(task_name: string): Promise<SystemTask> {
        return DefaultClient.fetch<SystemTask>(["admin", "system_tasks", task_name]);
    }

    static list(filter?: QueryArguments): Promise<SystemTask[]> {
        return DefaultClient.fetch<SystemTask[]>(["admin", "system_tasks"], filter);
    }

    static retry(task_name: string): string {
        return DefaultClient.makeUrl(["admin", "system_tasks", task_name, "retry"]);
    }

}
