import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

type PrimitiveName = 'string' | 'number' | 'boolean' | 'null' | 'any';

type TypeNode =
	| { kind: 'primitive'; name: PrimitiveName }
	| { kind: 'array'; element: TypeNode }
	| { kind: 'ref'; name: string }
	| { kind: 'union'; types: TypeNode[] }
	| { kind: 'record'; value: TypeNode };

interface ObjectSchema {
	name: string;
	props: Map<string, TypeNode>;
	propPresence: Map<string, number>;
	totalInstances: number;
	totalKeysCount: number;
	order: number;
}

const buffDataPath = path.join(__dirname, '../public/gamedata/battle/buff_template_data.json');
const buffData = JSON.parse(fs.readFileSync(buffDataPath, 'utf-8')) as Record<string, any>;

const schemas = new Map<string, ObjectSchema>();
let schemaOrder = 0;

const primitive = (name: PrimitiveName): TypeNode => ({ kind: 'primitive', name });

const isValidIdentifier = (key: string) => /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(key);

const toPascalCase = (input: string) => {
	const cleaned = input.replace(/[^A-Za-z0-9]+/g, ' ');
	return cleaned
		.split(' ')
		.filter(Boolean)
		.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
		.join('');
};

const makeTypeName = (pathParts: string[]) => toPascalCase(pathParts.join('_')) || 'Anonymous';

function mergeTypes(a: TypeNode, b: TypeNode): TypeNode {
	if (a.kind === 'union') {
		return mergeUnion(a.types, b);
	}
	if (b.kind === 'union') {
		return mergeUnion(b.types, a);
	}
	if (a.kind === 'primitive' && b.kind === 'primitive' && a.name === b.name) {
		return a;
	}
	if (a.kind === 'array' && b.kind === 'array') {
		return { kind: 'array', element: mergeTypes(a.element, b.element) };
	}
	if (a.kind === 'ref' && b.kind === 'ref' && a.name === b.name) {
		return a;
	}
	if (a.kind === 'record' && b.kind === 'record') {
		return { kind: 'record', value: mergeTypes(a.value, b.value) };
	}
	return mergeUnion([a], b);
}

function mergeUnion(types: TypeNode[], next: TypeNode): TypeNode {
	const all = [...types, next];
	const flattened: TypeNode[] = [];
	for (const t of all) {
		if (t.kind === 'union') {
			flattened.push(...t.types);
		} else {
			flattened.push(t);
		}
	}
	const deduped: TypeNode[] = [];
	for (const t of flattened) {
		if (!deduped.some((d) => isSameType(d, t))) {
			deduped.push(t);
		}
	}
	if (deduped.length === 1) {
		return deduped[0];
	}
	return { kind: 'union', types: deduped };
}

function isSameType(a: TypeNode, b: TypeNode): boolean {
	if (a.kind !== b.kind) return false;
	switch (a.kind) {
		case 'primitive':
			return a.name === (b as any).name;
		case 'array':
			return isSameType(a.element, (b as any).element);
		case 'ref':
			return a.name === (b as any).name;
		case 'record':
			return isSameType(a.value, (b as any).value);
		case 'union':
			return false;
	}
}

function ensureSchema(name: string): ObjectSchema {
	const existing = schemas.get(name);
	if (existing) return existing;
	const schema: ObjectSchema = {
		name,
		props: new Map(),
		propPresence: new Map(),
		totalInstances: 0,
		totalKeysCount: 0,
		order: schemaOrder++,
	};
	schemas.set(name, schema);
	return schema;
}

function inferValue(value: any, pathParts: string[]): TypeNode {
	if (value === null) return primitive('null');
	if (value === undefined) return primitive('any');
	if (typeof value === 'string') return primitive('string');
	if (typeof value === 'number') return primitive('number');
	if (typeof value === 'boolean') return primitive('boolean');
	if (Array.isArray(value)) {
		if (value.length === 0) {
			return { kind: 'array', element: primitive('any') };
		}
		let elementType = inferValue(value[0], [...pathParts, 'Item']);
		for (let i = 1; i < value.length; i += 1) {
			elementType = mergeTypes(elementType, inferValue(value[i], [...pathParts, 'Item']));
		}
		return { kind: 'array', element: elementType };
	}
	if (typeof value === 'object') {
		const typeName = makeTypeName(pathParts);
		const schema = ensureSchema(typeName);
		schema.totalInstances += 1;
		const keys = Object.keys(value);
		schema.totalKeysCount += keys.length;
		for (const key of keys) {
			schema.propPresence.set(key, (schema.propPresence.get(key) || 0) + 1);
			const inferred = inferValue(value[key], [...pathParts, key]);
			const existing = schema.props.get(key);
			schema.props.set(key, existing ? mergeTypes(existing, inferred) : inferred);
		}
		return { kind: 'ref', name: typeName };
	}
	return primitive('any');
}

function shouldUseRecord(schema: ObjectSchema): boolean {
	const uniqueKeys = schema.props.size;
	if (schema.totalInstances === 0) return false;
	const avgKeys = schema.totalKeysCount / schema.totalInstances;
	return uniqueKeys >= 30 && avgKeys <= uniqueKeys * 0.3;
}

function renderType(t: TypeNode): string {
	switch (t.kind) {
		case 'primitive':
			return t.name === 'null' ? 'null' : t.name;
		case 'array':
			return `${renderType(t.element)}[]`;
		case 'ref':
			return t.name;
		case 'record':
			return `Record<string, ${renderType(t.value)}>`;
		case 'union':
			return t.types.map(renderType).join(' | ');
	}
}

function renderSchema(schema: ObjectSchema): string {
	if (shouldUseRecord(schema)) {
		const valueTypes: TypeNode[] = [];
		for (const type of schema.props.values()) {
			valueTypes.push(type);
		}
		const union = valueTypes.reduce((acc, t) => (acc ? mergeTypes(acc, t) : t), null as any);
		const valueType = union || primitive('any');
		return `export type ${schema.name} = Record<string, ${renderType(valueType)}>;`;
	}

	const lines: string[] = [];
	lines.push(`export interface ${schema.name} {`);
	const keys = Array.from(schema.props.keys()).sort();
	for (const key of keys) {
		const type = schema.props.get(key)!;
		const presence = schema.propPresence.get(key) || 0;
		const optional = presence < schema.totalInstances;
		const propName = isValidIdentifier(key) ? key : JSON.stringify(key);
		lines.push(`  ${propName}${optional ? '?' : ''}: ${renderType(type)};`);
	}
	lines.push('}');
	return lines.join('\n');
}

// 构建 BuffTemplate schema
for (const value of Object.values(buffData)) {
	if (value && typeof value === 'object' && !Array.isArray(value)) {
		inferValue(value, ['BuffTemplate']);
	}
}

const orderedSchemas = Array.from(schemas.values()).sort((a, b) => a.order - b.order);

const outputLines: string[] = [];
outputLines.push('// Auto-generated from buff_template_data.json');
outputLines.push('// Base type: Record<string, BuffTemplate>');
outputLines.push('');

for (const schema of orderedSchemas) {
	outputLines.push(renderSchema(schema));
	outputLines.push('');
}

outputLines.push('export type BuffTemplateMap = Record<string, BuffTemplate>;');
outputLines.push('');

const outDir = path.join(__dirname, 'generated');
fs.mkdirSync(outDir, { recursive: true });

const outputPath = path.join(outDir, 'buff_template_interface.ts');
fs.writeFileSync(outputPath, outputLines.join('\n'), 'utf-8');

console.log(`✓ interface 已生成: ${outputPath}`);
