export interface JsonProperty {
  name: string;
  type: JsonPropertyType;
}

export enum JsonPropertyType {
  string = 'string',
  number = 'number',
}
