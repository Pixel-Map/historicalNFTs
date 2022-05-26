import { Injectable } from '@nestjs/common';
import { JSONSchema7 } from 'json-schema';
import { JsonProperty, JsonPropertyType } from './json.property.dto';
import path from 'path';
import Ajv from 'ajv';
import fs from 'fs';

@Injectable()
export class SchemaService {
  // Does the data provided match the expected schema?
  async isDataValid(folderPath, data) {
    const schema = await this.getSchema(folderPath);
    const ajv = new Ajv(); // options can be passed, e.g. {allErrors: true}
    const valid = ajv.validate(schema, data);
    if (!valid) console.log(ajv.errors);
    return valid;
  }

  getSchema(folderPath: string): JSONSchema7 {
    const schemaPath = folderPath + '/.schema.json';
    if (fs.existsSync(schemaPath)) {
      return JSON.parse(fs.readFileSync(folderPath + '/.schema.json', 'utf-8'));
    } else {
      return this.generateSchema(folderPath);
    }
  }

  generateSchema(folderPath: string): any {
    const folderName = folderPath.split('/').pop();
    const jsonData = this.loadJSONinFolder(folderPath);
    const commonProperties = this.getCommonPropertiesWithinArray(jsonData);
    if (commonProperties.length === 0) {
      return false;
    }
    const generatedProperties = {};
    for (const property of commonProperties) {
      switch (property.type) {
        case JsonPropertyType.string:
          generatedProperties[property.name] = {
            type: 'string',
            title: 'The ' + property.name + ' Schema',
            default: '',
            pattern: '^(.*)$',
          };
          break;
        case JsonPropertyType.number:
          generatedProperties[property.name] = {
            type: 'number',
            title: 'The ' + property.name + ' Schema',
            default: 0,
          };
          break;
      }
    }
    const schema = {
      definitions: {},
      $schema: 'http://json-schema.org/draft-07/schema#',
      $id: folderName,
      type: 'object',
      title: folderName,
      required: commonProperties.map(property => property.name),
      properties: generatedProperties,
    };
    return schema;
  }

  // Get common properties within an object array (key-value pair, value is type)
  getCommonPropertiesWithinArray(objectsArray): [JsonProperty?] {
    const commonProperties: [JsonProperty?] = [];
    const commonKeys = this.getCommonKeysWithinArrayOfObjects(objectsArray);

    for (const key of commonKeys) {
      commonProperties.push({
        name: key,
        type: JsonPropertyType[typeof objectsArray[0][key]],
      });
    }
    return commonProperties;
  }

  // Return all keys that are found in every object within an array.
  // If some objects are missing the key, it will not be returned
  getCommonKeysWithinArrayOfObjects(objectArray): string[] {
    // Get all unique keys across all Objects
    let allKeys = [];
    for (const object of objectArray) {
      if (Array.isArray(object)) {
        allKeys = [...new Set([...allKeys, ...Object.keys(object[0])])];
      } else {
        allKeys = [...new Set([...allKeys, ...Object.keys(object)])];
      }
    }
    const keysInAllObjects = [];
    for (const key of allKeys) {
      let foundWithinObjects = true;
      for (const object of objectArray) {
        if (Array.isArray(object)) {
          if (!Object.keys(object[0]).includes(key)) {
            foundWithinObjects = false;
          }
        } else {
          if (!Object.keys(object).includes(key)) {
            foundWithinObjects = false;
          }
        }
      }
      if (foundWithinObjects) {
        keysInAllObjects.push(key);
      }
    }
    return keysInAllObjects;
  }

  // Parse all JSON Files within a folder, return as Array of Objects
  loadJSONinFolder(folderPath: string): Record<string, any>[] {
    const filesNamesInFolder = fs.readdirSync(folderPath);
    const jsonFileNamesInFolder = filesNamesInFolder.filter(file => {
      return path.extname(file).toLowerCase() === '.json';
    });

    // Read in JSON data
    const parsedFiles = [];
    for (const fileName of jsonFileNamesInFolder) {
      const fileData = JSON.parse(
        fs.readFileSync(folderPath + '/' + fileName, 'utf8'),
      );
      parsedFiles.push(fileData);
    }

    return parsedFiles;
  }
}
